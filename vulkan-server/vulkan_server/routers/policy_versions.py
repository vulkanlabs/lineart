import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.orm import Session

from vulkan.exceptions import DataSourceNotFoundException
from vulkan.spec.nodes.base import NodeType
from vulkan_server import definitions, schemas
from vulkan_server.dagster.launch_run import (
    MAX_POLLING_TIMEOUT_MS,
    MIN_POLLING_INTERVAL_MS,
    DagsterRunLauncher,
    get_dagster_launcher,
    get_run_result,
)
from vulkan_server.dagster.service_client import (
    VulkanDagsterServiceClient,
    get_dagster_service_client,
)
from vulkan_server.db import (
    ConfigurationValue,
    DataSource,
    Policy,
    PolicyDataDependency,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    get_db,
)
from vulkan_server.events import VulkanEvent
from vulkan_server.logger import VulkanLogger, get_logger
from vulkan_server.utils import validate_date_range

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
):
    policy = db.query(Policy).filter_by(policy_id=config.policy_id).first()
    if policy is None:
        msg = f"Tried to create a version for non-existent policy {config.policy_id}"
        logger.system.error(msg)
        raise HTTPException(status_code=404, detail=msg)

    version = PolicyVersion(
        policy_id=config.policy_id,
        alias=config.alias,
        status=PolicyVersionStatus.INVALID,
        spec={"nodes": [], "input_schema": {}},
        input_schema={},
        requirements=[],
    )
    db.add(version)
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


@router.get("", response_model=list[schemas.PolicyVersion])
def list_policy_versions(
    policy_id: str | None = None,
    archived: bool = False,
    db: Session = Depends(get_db),
):
    stmt = select(PolicyVersion).where(PolicyVersion.archived == archived)
    if policy_id is not None:
        stmt = stmt.where(PolicyVersion.policy_id == policy_id)

    versions = db.execute(stmt).scalars().all()
    if len(versions) == 0:
        return Response(status_code=204)

    return versions


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

    # Update the policy version with the new spec and requirements
    spec = convert_pydantic_to_dict(config.spec)
    version.alias = config.alias
    version.input_schema = config.input_schema
    version.spec = spec
    version.requirements = config.requirements
    version.status = PolicyVersionStatus.INVALID
    version.ui_metadata = convert_pydantic_to_dict(config.ui_metadata)
    db.commit()

    data_input_nodes = [
        node
        for node in config.spec.nodes
        if node.node_type == NodeType.DATA_INPUT.value
    ]
    # List of data source names used in the data input nodes
    used_data_sources = [node.metadata["data_source"] for node in data_input_nodes]

    if used_data_sources:
        try:
            data_sources = _add_data_source_dependencies(db, version, used_data_sources)
        except DataSourceNotFoundException as e:
            err = "Failed to add data source dependencies"
            logger.system.error(
                f"{err} ({version.policy_version_id}): {e}", exc_info=True
            )
            msg = f"{err}. Policy Version ID: {version.policy_version_id}"
            raise HTTPException(status_code=500, detail={"msg": msg}) from e

        # Check if the data source's required runtime params are configured
        # in the node parameters field.
        for node in data_input_nodes:
            ds = data_sources[node.metadata["data_source"]]
            if ds.runtime_params is not None:
                configured_params = node.metadata["parameters"].keys()
                if set(ds.runtime_params) != set(configured_params):
                    msg = (
                        f"Data source {ds.name} requires runtime parameters "
                        f"{ds.runtime_params} but got {list(configured_params)} "
                        f"from {node.name}"
                    )
                    raise HTTPException(status_code=400, detail={"msg": msg})

    config_variables = config.spec.config_variables or None
    if config_variables is not None:
        version.variables = config_variables

    # Ensure the workspace is created or updated with the new spec and requirements
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
        dagster_service_client.ensure_workspace_added(str(version.policy_version_id))
        version.status = PolicyVersionStatus.VALID
    except ValueError as e:
        logger.system.error(
            f"Failed to update workspace ({version.policy_version_id}), version is invalid:\n{e}",
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
) -> dict[str, DataSource]:
    q = select(
        DataSource,
    ).where(
        DataSource.name.in_(data_sources),
        DataSource.archived.is_(False),
    )
    matched = db.execute(q).scalars().all()
    missing = list(set(data_sources) - set([m.name for m in matched]))
    if missing:
        msg = f"The following data sources are not defined: {missing}"
        raise DataSourceNotFoundException(msg)

    for m in matched:
        dependency = PolicyDataDependency(
            data_source_id=m.data_source_id,
            policy_version_id=version.policy_version_id,
        )
        db.add(dependency)

    return {str(m.name): m for m in matched}


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
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
):
    run = launcher.create_run(
        input_data=input_data,
        policy_version_id=policy_version_id,
        run_config_variables=config_variables,
    )
    return {"policy_version_id": policy_version_id, "run_id": run.run_id}


@router.post("/{policy_version_id}/run", response_model=schemas.RunResult)
async def run_workflow(
    policy_version_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    polling_interval_ms: int = MIN_POLLING_INTERVAL_MS,
    polling_timeout_ms: int = MAX_POLLING_TIMEOUT_MS,
    db: Session = Depends(get_db),
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
):
    run = launcher.create_run(
        input_data=input_data,
        policy_version_id=policy_version_id,
        run_config_variables=config_variables,
    )
    result = await get_run_result(
        db, run.run_id, polling_interval_ms, polling_timeout_ms
    )
    return result


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

    required_variables = version.variables or []
    variables = (
        db.query(ConfigurationValue)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )
    variable_map = {v.name: v for v in variables}

    result = []
    for variable in variables:
        entry = {
            "name": variable.name,
            "value": variable.value,
            "created_at": variable.created_at,
            "last_updated_at": variable.last_updated_at,
        }
        result.append(entry)

    # If the variable is not in the database, even if they're null.
    for variable in required_variables:
        if variable not in variable_map:
            entry = {
                "name": variable,
                "value": None,
                "created_at": None,
                "last_updated_at": None,
            }
            result.append(entry)

    return result


@router.put("/{policy_version_id}/variables")
def set_config_variables(
    policy_version_id: str,
    desired_variables: Annotated[list[schemas.ConfigurationVariablesBase], Body()],
    db: Session = Depends(get_db),
    logger: VulkanLogger = Depends(get_logger),
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

    existing_variables = (
        db.query(ConfigurationValue)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )

    for v in existing_variables:
        if v.name not in set([var.name for var in desired_variables]):
            db.delete(v)

    existing_variables_map = {v.name: v for v in existing_variables}
    for v in desired_variables:
        config_value = existing_variables_map.get(v.name, None)
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
    logger.event(
        VulkanEvent.POLICY_VERSION_VARIABLES_UPDATED,
        policy_version_id=policy_version_id,
        variables=[v.model_dump_json() for v in desired_variables],
    )
    return {"policy_version_id": policy_version_id, "variables": desired_variables}


@router.get("/{policy_version_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy_version(
    policy_version_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = validate_date_range(start_date, end_date)
    q = (
        select(Run)
        .filter(
            (Run.policy_version_id == policy_version_id)
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .order_by(Run.created_at.desc())
    )
    runs = db.execute(q).scalars().all()
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
