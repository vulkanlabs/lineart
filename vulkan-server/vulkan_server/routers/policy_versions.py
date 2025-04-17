from dataclasses import dataclass
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from vulkan_public.exceptions import DataSourceNotFoundException
from vulkan_public.spec.nodes.base import NodeType

from vulkan_server import definitions, schemas
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import create_run
from vulkan_server.dagster.service_client import (
    VulkanDagsterServiceClient,
    get_dagster_service_client,
)
from vulkan_server.db import (
    BeamWorkspace,
    ConfigurationValue,
    DataSource,
    Policy,
    PolicyDataDependency,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    WorkspaceStatus,
    get_db,
)
from vulkan_server.events import VulkanEvent
from vulkan_server.exceptions import VulkanServerException
from vulkan_server.logger import VulkanLogger, get_logger
from vulkan_server.services.resolution import (
    ResolutionServiceClient,
    get_resolution_service_client,
)

router = APIRouter(
    prefix="/policy-versions",
    tags=["policy-versions"],
    responses={404: {"description": "Not found"}},
)


@router.post("", response_model=schemas.PolicyVersion)
def create_policy_version(
    config: schemas.PolicyVersionCreate,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
    dagster_service_client: VulkanDagsterServiceClient = Depends(
        get_dagster_service_client
    ),
):
    extra = {"policy_id": config.policy_id, "policy_version_alias": config.alias}
    logger.system.debug("Creating policy version", extra={"extra": extra})

    policy = db.query(Policy).filter_by(policy_id=config.policy_id).first()
    if policy is None:
        msg = f"Tried to create a version for non-existent policy {config.policy_id}"
        logger.system.error(msg)
        raise HTTPException(status_code=404, detail=msg)

    spec = convert_pydantic_to_dict(config.spec)
    version = PolicyVersion(
        policy_id=config.policy_id,
        alias=config.alias,
        spec=spec,
        requirements=config.requirements,
        input_schema=config.input_schema,
        status=PolicyVersionStatus.INVALID,
    )
    db.add(version)
    db.commit()

    data_sources = [
        node.metadata["data_source"]
        for node in config.spec.nodes
        if node.node_type == NodeType.DATA_INPUT.value
    ]
    if data_sources:
        try:
            _add_data_source_dependencies(db, version, data_sources)
        except DataSourceNotFoundException as e:
            err = "Failed to add data source dependencies"
            logger.system.error(
                f"{err} ({version.policy_version_id}): {e}", exc_info=True
            )
            msg = f"{err}. Policy Version ID: {version.policy_version_id}"
            raise HTTPException(status_code=500, detail={"msg": msg}) from e

    try:
        dagster_service_client.update_workspace(
            workspace_id=version.policy_version_id,
            spec=spec,
            requirements=config.requirements,
        )
    except (ValueError, VulkanServerException) as e:
        logger.system.error(
            f"Failed to create workspace ({version.policy_version_id}): {e}",
            exc_info=True,
        )
        msg = (
            "Failed to create policy version workspace. "
            f"Policy Version ID: {version.policy_version_id}"
        )
        raise HTTPException(status_code=500, detail={"msg": msg}) from e

    try:
        dagster_service_client.ensure_workspace_added(str(version.policy_version_id))
    except ValueError:
        logger.system.error(
            f"Failed to create workspace ({version.policy_version_id}), version is invalid",
            exc_info=True,
        )

    db.commit()

    logger.event(
        VulkanEvent.POLICY_VERSION_CREATED,
        policy_id=config.policy_id,
        policy_version_id=version.policy_version_id,
        policy_version_alias=config.alias,
    )

    return version


@router.get("/{policy_version_id}", response_model=schemas.PolicyVersion)
def get_policy_version(
    policy_version_id: str,
    db: Session = Depends(get_db),
):
    policy_version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if policy_version is None:
        return Response(status_code=204)
    return policy_version


@router.put("/{policy_version_id}", response_model=schemas.PolicyVersion)
def update_policy_version(
    policy_version_id: str,
    config: schemas.PolicyVersionBase,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
    dagster_service_client: VulkanDagsterServiceClient = Depends(
        get_dagster_service_client
    ),
):
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
            archived=False,
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)
    spec = convert_pydantic_to_dict(config.spec)

    extra = {"policy_version_id": policy_version_id, "spec": spec}
    logger.system.debug("Updating policy version", extra={"extra": extra})
    # TODO: any simpler way to do this?
    # Update the policy version with the new spec and requirements
    version.alias = config.alias
    version.input_schema = config.input_schema
    version.spec = spec
    version.requirements = config.requirements
    version.status = PolicyVersionStatus.INVALID
    version.ui_metadata = convert_pydantic_to_dict(config.ui_metadata)
    db.commit()

    # Update the workspace with the new spec and requirements
    try:
        dagster_service_client.update_workspace(
            workspace_id=version.policy_version_id,
            spec=spec,
            requirements=config.requirements,
        )
    except ValueError as e:
        logger.system.error(
            f"Failed to update workspace ({version.policy_version_id}): {e}",
            exc_info=True,
        )
        msg = (
            "Failed to update policy version workspace. "
            f"Policy Version ID: {version.policy_version_id}"
        )
        raise HTTPException(status_code=500, detail={"msg": msg}) from e

    try:
        dagster_service_client.ensure_workspace_added(version.policy_version_id)
        version.status = PolicyVersionStatus.VALID
    except ValueError:
        logger.system.error(
            f"Failed to update workspace ({version.policy_version_id}), version is invalid",
            exc_info=False,
        )

    db.commit()
    logger.event(
        VulkanEvent.POLICY_VERSION_UPDATED,
        policy_id=version.policy_id,
        policy_version_id=policy_version_id,
        policy_version_alias=version.alias,
    )
    return version


def _add_data_source_dependencies(
    db: Session, version: PolicyVersion, data_sources: list[str]
) -> list[DataSource]:
    matched = (
        db.query(DataSource)
        .filter(
            DataSource.name.in_(data_sources),
            DataSource.archived.is_(False),
        )
        .all()
    )
    missing = list(set(data_sources) - set([m.name for m in matched]))
    if missing:
        raise DataSourceNotFoundException(
            msg=f"The following data sources are not defined: {missing}"
        )

    for m in matched:
        dependency = PolicyDataDependency(
            data_source_id=m.data_source_id,
            policy_version_id=version.policy_version_id,
        )
        db.add(dependency)

    return matched


@dataclass
class PolicyVersionSettings:
    module_name: str
    input_schema: dict[str, str]
    graph_definition: str
    workspace_path: str
    image_path: str
    config_variables: list[str] | None = None
    data_sources: list[str] | None = None


@router.delete("/{policy_version_id}")
def delete_policy_version(
    policy_version_id: str,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
    dagster_launcher_client: VulkanDagsterServiceClient = Depends(
        get_dagster_service_client
    ),
):
    # TODO: ensure this function can only be executed by ADMIN level users
    policy_version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if policy_version is None or policy_version.archived:
        msg = f"Tried to delete non-existent policy version {policy_version_id}"
        raise HTTPException(status_code=404, detail=msg)

    # Ensure this policy version is not being used by its Policy's current
    # allocation strategy.
    policy: Policy = (
        db.query(Policy).filter_by(policy_id=policy_version.policy_id).first()
    )
    if policy.allocation_strategy is not None:
        strategy = schemas.PolicyAllocationStrategy.model_validate(
            policy.allocation_strategy
        )
        active_versions = [opt.policy_version_id for opt in strategy.choice]
        if strategy.shadow is not None:
            active_versions += [strategy.shadow.policy_version_id]

        if policy_version_id in active_versions:
            msg = (
                f"Policy version {policy_version_id} is currently in use by the policy "
                f"allocation strategy for policy {policy.policy_id}"
            )
            raise HTTPException(status_code=400, detail=msg)

    name = definitions.version_name(policy_version_id)
    try:
        dagster_launcher_client.delete_workspace(name)
        dagster_launcher_client.ensure_workspace_removed(name)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting policy version {policy_version_id}: {str(e)}",
        )

    policy_version.archived = True
    db.commit()

    logger.event(
        VulkanEvent.POLICY_VERSION_DELETED, policy_version_id=policy_version_id
    )
    return {"policy_version_id": policy_version_id}


@router.post("/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
):
    try:
        run = create_run(
            db=db,
            dagster_client=dagster_client,
            server_url=server_config.server_url,
            policy_version_id=policy_version_id,
            input_data=input_data,
            run_config_variables=config_variables,
        )
    except VulkanServerException as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "msg": e.msg,
            },
        )

    return {"policy_version_id": policy_version_id, "run_id": run.run_id}


@router.get(
    "/{policy_version_id}/variables",
    response_model=list[schemas.ConfigurationVariables],
)
def list_config_variables(
    policy_version_id: str,
    db: Session = Depends(get_db),
):
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
            archived=False,
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)

    required_variables = version.variables
    if required_variables is None:
        return Response(status_code=204)

    variables = (
        db.query(ConfigurationValue)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )
    variable_map = {v.name: v for v in variables}

    result = []
    for variable_name in required_variables:
        entry = {"name": variable_name}
        if variable_name in variable_map:
            entry["value"] = variable_map[variable_name].value
            entry["created_at"] = variable_map[variable_name].created_at
            entry["last_updated_at"] = variable_map[variable_name].last_updated_at
        result.append(entry)

    return result


@router.put("/{policy_version_id}/variables")
def set_config_variables(
    policy_version_id: str,
    variables: Annotated[list[schemas.ConfigurationVariablesBase], Body()],
    db: Session = Depends(get_db),
):
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
            archived=False,
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)

    for v in variables:
        config_value = (
            db.query(ConfigurationValue)
            .filter_by(policy_version_id=policy_version_id, name=v.name)
            .first()
        )

        if config_value is None:
            config_value = ConfigurationValue(
                policy_version_id=policy_version_id,
                name=v.name,
                value=v.value,
            )
            db.add(config_value)
        else:
            config_value.value = v.value

    db.commit()
    return {"policy_version_id": policy_version_id, "variables": variables}


@router.get("/{policy_version_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy_version(policy_version_id: str, db: Session = Depends(get_db)):
    runs = db.query(Run).filter_by(policy_version_id=policy_version_id).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.get(
    "/{policy_version_id}/data-sources",
    response_model=list[schemas.DataSourceReference],
)
def list_data_sources_by_policy_version(
    policy_version_id: str,
    db: Session = Depends(get_db),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
        )
        .first()
    )
    if policy_version is None:
        raise HTTPException(status_code=404, detail="Policy version not found")

    data_source_uses = (
        db.query(PolicyDataDependency)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )
    if len(data_source_uses) == 0:
        return Response(status_code=204)

    data_sources = []
    for use in data_source_uses:
        ds: DataSource = (
            db.query(DataSource).filter_by(data_source_id=use.data_source_id).first()
        )
        data_sources.append(
            schemas.DataSourceReference(
                data_source_id=ds.data_source_id,
                name=ds.name,
                created_at=ds.created_at,
            )
        )

    return data_sources


@router.get(
    "/{policy_version_id}/backtest-workspace", response_model=schemas.BeamWorkspace
)
def get_beam_workspace(
    policy_version_id: str,
    db=Depends(get_db),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
        )
        .first()
    )
    if policy_version is None:
        return Response(status_code=204)

    workspace = (
        db.query(BeamWorkspace).filter_by(policy_version_id=policy_version_id).first()
    )
    if workspace is None:
        return Response(status_code=204)

    return workspace


@router.post(
    "/{policy_version_id}/backtest-workspace", response_model=schemas.BeamWorkspace
)
def create_beam_workspace(
    policy_version_id: str,
    logger: VulkanLogger = Depends(get_logger),
    db: Session = Depends(get_db),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
):
    # If a workspace exists, this is a no-op.
    current_workspace = (
        db.query(BeamWorkspace).filter_by(policy_version_id=policy_version_id).first()
    )
    if current_workspace is not None:
        return current_workspace

    policy_version: PolicyVersion = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
        )
        .first()
    )

    beam_workspace = BeamWorkspace(
        policy_version_id=policy_version.policy_version_id,
        status=WorkspaceStatus.CREATION_PENDING,
    )
    db.add(beam_workspace)
    db.commit()

    try:
        response = resolution_service.create_beam_workspace(
            policy_version_id=str(policy_version_id),
            base_image=policy_version.base_worker_image,
        )

        beam_workspace.image = response.json()["image_path"]
        beam_workspace.status = WorkspaceStatus.OK
    except Exception as e:
        beam_workspace.status = WorkspaceStatus.CREATION_FAILED
        logger.system.error(
            f"Failed to create workspace ({policy_version_id}): {e}", exc_info=True
        )
        msg = (
            "This is usually an issue with Vulkan's internal services. "
            "Contact support for assistance. "
            f"Workspace ID: {policy_version_id}"
        )
        raise HTTPException(status_code=500, detail={"msg": msg})
    finally:
        db.commit()

    logger.event(
        VulkanEvent.BEAM_WORKSPACE_CREATED, policy_version_id=policy_version_id
    )
    return beam_workspace


def convert_pydantic_to_dict(obj):
    """Recursively convert Pydantic models to dictionaries."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif isinstance(obj, dict):
        return {k: convert_pydantic_to_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [convert_pydantic_to_dict(i) for i in obj]
    else:
        return obj
