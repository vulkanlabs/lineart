import datetime
import json
from dataclasses import dataclass
from itertools import chain
from typing import Annotated, Any

import pandas as pd
import sqlalchemy.exc
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.orm import Session
from vulkan_public.exceptions import (
    UNHANDLED_ERROR_NAME,
    ComponentNotFoundException,
    DataSourceNotFoundException,
    VulkanInternalException,
)

from vulkan.core.run import RunStatus
from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import create_run
from vulkan_server.dagster.service_client import (
    VulkanDagsterServiceClient,
    get_dagster_service_client,
)
from vulkan_server.db import (
    ComponentVersion,
    ComponentVersionDependency,
    DagsterWorkspace,
    DataSource,
    Policy,
    PolicyDataDependency,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    WorkspaceStatus,
    get_db,
)
from vulkan_server.exceptions import ExceptionHandler, VulkanServerException
from vulkan_server.logger import init_logger
from vulkan_server.services.resolution import (
    ResolutionServiceClient,
    get_resolution_service_client,
)

logger = init_logger("policies")
router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Policy])
def list_policies(
    project_id: str = Depends(get_project_id),
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = dict(project_id=project_id)
    if not include_archived:
        filters["archived"] = False

    policies = db.query(Policy).filter_by(**filters).all()
    if len(policies) == 0:
        return Response(status_code=204)
    return policies


@router.post("/")
def create_policy(
    config: schemas.PolicyBase,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy = Policy(project_id=project_id, **config.model_dump())
    db.add(policy)
    db.commit()
    logger.info(f"Policy {config.name} created")
    return {"policy_id": policy.policy_id, "name": policy.name}


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(
    policy_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy).filter_by(policy_id=policy_id, project_id=project_id).first()
    )
    if policy is None:
        return Response(status_code=404)
    return policy


@router.put("/{policy_id}")
def update_policy(
    policy_id: str,
    config: schemas.PolicyUpdate,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy).filter_by(policy_id=policy_id, project_id=project_id).first()
    )
    if policy is None:
        msg = f"Tried to update non-existent policy {policy_id}"
        raise HTTPException(status_code=404, detail=msg)

    if (
        config.active_policy_version_id is not None
        and config.active_policy_version_id != policy.active_policy_version_id
    ):
        policy_version = (
            db.query(PolicyVersion)
            .filter_by(
                policy_version_id=config.active_policy_version_id, project_id=project_id
            )
            .first()
        )
        if policy_version is None:
            msg = f"Tried to use non-existent version {config.active_policy_version_id} for policy {policy_id}"
            raise HTTPException(status_code=404, detail=msg)

        if policy_version.status != PolicyVersionStatus.VALID:
            msg = f"Tried to use invalid version {config.active_policy_version_id} for policy {policy_id}"
            raise HTTPException(status_code=400, detail=msg)

        policy.active_policy_version_id = config.active_policy_version_id

    if config.active_policy_version_id is None:
        policy.active_policy_version_id = None

    if config.name is not None and config.name != policy.name:
        policy.name = config.name
    if config.description is not None and config.description != policy.description:
        policy.description = config.description

    db.commit()
    msg = f"Policy {policy_id} updated"
    logger.info(msg)
    return {
        "policy_id": policy.policy_id,
        "active_policy_version_id": policy.active_policy_version_id,
    }


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy = (
        db.query(Policy).filter_by(policy_id=policy_id, project_id=project_id).first()
    )
    if policy is None or policy.archived:
        msg = f"Tried to delete non-existent policy {policy_id}"
        raise HTTPException(status_code=404, detail=msg)

    policy_versions = (
        db.query(PolicyVersion)
        .filter_by(policy_id=policy_id, project_id=project_id, archived=False)
        .all()
    )
    if len(policy_versions) > 0:
        msg = f"Policy {policy_id} has associated versions, delete them first"
        raise HTTPException(status_code=400, detail=msg)

    policy.archived = True
    db.commit()
    logger.info(f"Policy {policy_id} deleted")
    return {"policy_id": policy_id}


@router.get(
    "/{policy_id}/versions",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(
    policy_id: str,
    include_archived: bool = False,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    filters = dict(
        policy_id=policy_id,
        project_id=project_id,
        status=PolicyVersionStatus.VALID,
    )
    if not include_archived:
        filters["archived"] = False

    policy_versions = db.query(PolicyVersion).filter_by(**filters).all()
    if len(policy_versions) == 0:
        return Response(status_code=204)
    return policy_versions


@router.get("/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(
    policy_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy_versions = (
        db.query(PolicyVersion)
        .filter_by(policy_id=policy_id, project_id=project_id)
        .all()
    )
    policy_version_ids = [v.policy_version_id for v in policy_versions]
    runs = db.query(Run).filter(Run.policy_version_id.in_(policy_version_ids)).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.post("/{policy_id}/runs")
def create_run_by_policy(
    policy_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=list)],
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    try:
        policy = (
            db.query(Policy)
            .filter_by(policy_id=policy_id, project_id=project_id)
            .first()
        )
    except sqlalchemy.exc.DataError:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Invalid policy_id: {policy_id}",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Failed to get policy: {str(e)}",
            },
        )

    if policy is None:
        raise HTTPException(status_code=404, detail=f"Policy {policy_id} not found")
    if policy.active_policy_version_id is None:
        raise HTTPException(
            status_code=400,
            detail=f"Policy {policy_id} has no active version",
        )

    try:
        run = create_run(
            db=db,
            dagster_client=dagster_client,
            server_url=server_config.server_url,
            policy_version_id=policy.active_policy_version_id,
            project_id=project_id,
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

    return {"policy_id": policy.policy_id, "run_id": run.run_id}


@router.post("/{policy_id}/versions")
def create_policy_version(
    policy_id: str,
    config: schemas.PolicyVersionCreate,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
    dagster_launcher_client: VulkanDagsterServiceClient = Depends(
        get_dagster_service_client
    ),
):
    handler = ExceptionHandler(
        logger=logger,
        base_msg=(
            f"Failed to create workspace for policy {policy_id} version {config.alias}"
        ),
    )

    logger.info(f"Creating policy version for policy {policy_id}")
    if config.alias is None:
        # We can use the repo version as an easy alias or generate one.
        # This should ideally be a commit hash or similar, indicating a
        # unique version of the code.
        config.alias = config.repository_version

    policy = (
        db.query(Policy).filter_by(policy_id=policy_id, project_id=project_id).first()
    )
    if policy is None:
        msg = f"Tried to create a version for non-existent policy {policy_id}"
        handler.raise_exception(400, UNHANDLED_ERROR_NAME, msg)

    version = PolicyVersion(
        policy_id=policy_id,
        alias=config.alias,
        repository=config.repository,
        repository_version=config.repository_version,
        status=PolicyVersionStatus.INVALID,
        project_id=project_id,
    )
    db.add(version)
    db.commit()

    version_name = definitions.version_name(policy_id, version.policy_version_id)

    try:
        settings = _create_policy_version_workspace(
            resolution=resolution_service,
            name=version_name,
            repository=config.repository,
        )
        variables = settings.config_variables or []
        logger.debug("Workspace created")
    except Exception as e:
        if isinstance(e, VulkanInternalException):
            handler.raise_exception(400, e.__class__.__name__, str(e), e.metadata)
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, str(e))

    try:
        if settings.required_components:
            added_components = _add_component_dependencies(
                db, version, settings.required_components
            )
            inner_variables = [c.variables for c in added_components if c.variables]
            variables += list(chain.from_iterable(inner_variables))
        logger.debug("Processed components")

        if settings.data_sources:
            added_sources = _add_data_source_dependencies(
                db, version, settings.data_sources
            )
            inner_variables = [ds.variables for ds in added_sources if ds.variables]
            variables += list(chain.from_iterable(inner_variables))
        logger.debug("Processed data sources")

        if len(variables) > 0:
            version.variables = list(set(variables))
        logger.debug("Processed variables")

        version.input_schema = settings.input_schema
        version.graph_definition = json.dumps(settings.graph_definition)
        version.module_name = settings.module_name
        version.base_worker_image = settings.image_path
    except Exception as e:
        if isinstance(e, VulkanInternalException):
            handler.raise_exception(400, e.__class__.__name__, str(e), e.metadata)
        resolution_service.delete_workspace(version_name)
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, str(e))
    finally:
        db.commit()

    # Dagster-specific
    dagster_workspace = DagsterWorkspace(
        policy_version_id=version.policy_version_id,
        status=WorkspaceStatus.CREATION_PENDING,
        path=settings.workspace_path,
    )
    db.add(dagster_workspace)
    db.commit()

    try:
        dagster_launcher_client.create_workspace(
            version_name, version.repository, settings.required_components
        )
        dagster_launcher_client.ensure_workspace_added(version_name)

        dagster_workspace.status = WorkspaceStatus.OK
        db.commit()
        logger.debug("Updated Dagster repositories")
    except Exception as e:
        dagster_workspace.status = WorkspaceStatus.CREATION_FAILED
        db.commit()
        resolution_service.delete_workspace(version_name)

        if isinstance(e, VulkanInternalException):
            handler.raise_exception(400, e.__class__.__name__, str(e), e.metadata)
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, str(e))
    # END of Dagster-specific segment

    version.status = PolicyVersionStatus.VALID
    db.commit()
    logger.info(
        f"Policy version {config.alias} created for policy {policy_id} with "
        f"status {version.status}"
    )

    return {
        "policy_id": policy_id,
        "policy_version_id": version.policy_version_id,
        "alias": version.alias,
        "status": version.status.value,
    }


def _add_component_dependencies(
    db: Session, version: PolicyVersion, required_components: list[str]
) -> list[ComponentVersion]:
    matched = (
        db.query(ComponentVersion)
        .filter(
            ComponentVersion.alias.in_(required_components),
            ComponentVersion.project_id == version.project_id,
            ComponentVersion.archived == False,  # noqa: E712
        )
        .all()
    )
    missing = list(set(required_components) - set([m.alias for m in matched]))
    if missing:
        raise ComponentNotFoundException(
            msg=f"The following components are not defined: {missing}"
        )

    for m in matched:
        dependency = ComponentVersionDependency(
            component_version_id=m.component_version_id,
            policy_version_id=version.policy_version_id,
        )
        db.add(dependency)

    return matched


def _add_data_source_dependencies(
    db: Session, version: PolicyVersion, data_sources: list[str]
) -> list[DataSource]:
    matched = (
        db.query(DataSource)
        .filter(
            DataSource.name.in_(data_sources),
            DataSource.project_id == version.project_id,
            DataSource.archived == False,  # noqa: E712
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
    required_components: list[str] | None = None
    config_variables: list[str] | None = None
    data_sources: list[str] | None = None


def _create_policy_version_workspace(
    resolution: ResolutionServiceClient,
    name: str,
    repository: str,
) -> PolicyVersionSettings:
    try:
        response = resolution.create_workspace(name=name, repository=repository)
        response_data = response.json()
    except Exception as e:
        raise e

    definition_settings = response_data["policy_definition_settings"]

    version_settings = PolicyVersionSettings(
        module_name=response_data["module_name"],
        input_schema=response_data["input_schema"],
        graph_definition=response_data["graph_definition"],
        data_sources=response_data.get("data_sources", []),
        required_components=definition_settings.get("required_components", []),
        config_variables=definition_settings.get("config_variables", []),
        workspace_path=response_data["workspace_path"],
        image_path=response_data["image_path"],
    )
    return version_settings


def _validate_date_range(
    start_date: datetime.date | None,
    end_date: datetime.date | None,
):
    if start_date is None:
        start_date = datetime.date.today() - datetime.timedelta(days=30)
    if end_date is None:
        end_date = datetime.date.today()
    return start_date, end_date


@router.get("/{policy_id}/runs/duration", response_model=list[Any])
def run_duration_stats_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _validate_date_range(start_date, end_date)
    policy_versions = (
        db.query(PolicyVersion.policy_version_id).filter_by(policy_id=policy_id).all()
    )
    policy_version_ids = [v.policy_version_id for v in policy_versions]

    duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
    date_clause = F.DATE(Run.created_at).label("date")

    query = (
        db.query(
            date_clause,
            F.avg(duration_seconds).label("avg_duration"),
            F.min(duration_seconds).label("min_duration"),
            F.max(duration_seconds).label("max_duration"),
        )
        .filter(
            (Run.policy_version_id.in_(policy_version_ids))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
    )
    df = pd.read_sql(query.statement, query.session.bind)
    return df.to_dict(orient="records")


@router.get("/{policy_id}/runs/duration/by_status", response_model=list[Any])
def run_duration_stats_by_policy_status(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _validate_date_range(start_date, end_date)
    policy_versions = (
        db.query(PolicyVersion.policy_version_id).filter_by(policy_id=policy_id).all()
    )
    policy_version_ids = [v.policy_version_id for v in policy_versions]

    duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
    date_clause = F.DATE(Run.created_at).label("date")

    query = (
        db.query(
            date_clause,
            Run.status,
            F.avg(duration_seconds).label("avg_duration"),
        )
        .filter(
            (Run.policy_version_id.in_(policy_version_ids))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause, Run.status)
    )
    df = pd.read_sql(query.statement, query.session.bind)
    df = df.pivot(
        index=date_clause.name, values="avg_duration", columns=["status"]
    ).reset_index()
    return df.to_dict(orient="records")


@router.get("/{policy_id}/runs/count", response_model=list[Any])
def count_runs_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _validate_date_range(start_date, end_date)

    date_clause = F.DATE(Run.created_at).label("date")

    policy_versions = (
        db.query(PolicyVersion.policy_version_id).filter_by(policy_id=policy_id).all()
    )
    policy_version_ids = [v.policy_version_id for v in policy_versions]

    query = (
        db.query(
            date_clause,
            F.count(Run.run_id).label("count"),
        )
        .filter(
            (Run.policy_version_id.in_(policy_version_ids))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
    )
    df = pd.read_sql(query.statement, query.session.bind)
    return df.to_dict(orient="records")


@router.get("/{policy_id}/runs/errors", response_model=list[Any])
def error_rate_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    db: Session = Depends(get_db),
):
    start_date, end_date = _validate_date_range(start_date, end_date)

    date_clause = F.DATE(Run.created_at).label("date")
    q = (
        select(
            date_clause,
            F.count(Run.run_id).label("count"),
            (
                100
                * F.count(Run.run_id).filter(Run.status == RunStatus.FAILURE)
                / F.count(Run.run_id)
            ).label("error_rate"),
        )
        .where(
            (
                Run.policy_version_id.in_(
                    select(PolicyVersion.policy_version_id).where(
                        PolicyVersion.policy_id == policy_id
                    )
                )
            )
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause)
    )
    df = pd.read_sql(q, db.bind)
    return df.to_dict(orient="records")
