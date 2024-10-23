import datetime
import json
from typing import Annotated, Any

import pandas as pd
import sqlalchemy.exc
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy import func as F
from sqlalchemy.orm import Session
from vulkan_public.exceptions import (
    UNHANDLED_ERROR_NAME,
    VULKAN_INTERNAL_EXCEPTIONS,
    ComponentNotFoundException,
    VulkanInternalException,
)

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import create_run
from vulkan_server.dagster.trigger_run import update_repository
from vulkan_server.db import (
    ComponentVersion,
    ComponentVersionDependency,
    DagsterWorkspace,
    DagsterWorkspaceStatus,
    Policy,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    get_db,
)
from vulkan_server.exceptions import ExceptionHandler, VulkanServerException
from vulkan_server.logger import init_logger
from vulkan_server.services import VulkanDagsterServerClient

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
    input_data: Annotated[str, Body(embed=True)],
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    try:
        input_data_obj = json.loads(input_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Invalid input data: {str(e)}",
            },
        )

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
            input_data=input_data_obj,
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
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
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
    vulkan_dagster_client = VulkanDagsterServerClient(
        project_id=project_id, server_url=server_config.vulkan_dagster_server_url
    )

    try:
        workspace, required_components, config_variables = (
            _create_policy_version_workspace(
                db=db,
                vulkan_dagster_client=vulkan_dagster_client,
                policy_version_id=version.policy_version_id,
                name=version_name,
                repository=config.repository,
            )
        )
        if config_variables is not None:
            if not isinstance(config_variables, list) or not (
                all(isinstance(i, str) for i in config_variables)
            ):
                raise ValueError("config_variables must be a list of strings")
            version.variables = config_variables

        if required_components:
            matched = (
                db.query(ComponentVersion)
                # TODO: only within project!
                .filter(ComponentVersion.alias.in_(required_components))
                .all()
            )
            missing = list(set(required_components) - set([m.alias for m in matched]))
            if missing:
                raise ComponentNotFoundException(
                    msg=f"The following components are not defined: {missing}",
                    metadata={"components": missing},
                )

            for m in matched:
                dependency = ComponentVersionDependency(
                    component_version_id=m.component_version_id,
                    policy_version_id=version.policy_version_id,
                )
                db.add(dependency)

        graph = _install_policy_version_workspace(
            db=db,
            vulkan_dagster_client=vulkan_dagster_client,
            name=version_name,
            required_components=required_components,
            workspace=workspace,
        )
    except VulkanInternalException as e:
        error_name = VULKAN_INTERNAL_EXCEPTIONS[e.exit_status].__name__
        handler.raise_exception(400, error_name, str(e), e.metadata)
    except Exception as e:
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, str(e))
    finally:
        db.commit()

    logger.info(
        f"Creating version {version.policy_version_id} ({config.alias}) "
        f"for policy {policy_id}"
    )

    loaded_repos = update_repository(dagster_client)
    if loaded_repos.get(version_name, False) is False:
        msg = (
            f"Failed to load repository {version_name}.\n"
            f"Repository load status: {loaded_repos}"
        )
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, msg)

    version.status = PolicyVersionStatus.VALID
    version.graph_definition = json.dumps(graph)
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


def _create_policy_version_workspace(
    db: Session,
    vulkan_dagster_client: VulkanDagsterServerClient,
    policy_version_id: int,
    name: str,
    repository: str,
):
    workspace = DagsterWorkspace(
        policy_version_id=policy_version_id,
        status=DagsterWorkspaceStatus.CREATION_PENDING,
    )
    db.add(workspace)
    db.commit()

    try:
        response = vulkan_dagster_client.create_workspace(
            name=name, repository=repository
        )
    except Exception as e:
        workspace.status = DagsterWorkspaceStatus.CREATION_FAILED
        db.commit()
        raise e

    response_data = response.json()
    workspace.path = response_data["workspace_path"]
    db.commit()
    policy_settings = response_data["policy_definition_settings"]

    return (
        workspace,
        policy_settings["required_components"],
        policy_settings["config_variables"],
    )


def _install_policy_version_workspace(
    db: Session,
    vulkan_dagster_client: VulkanDagsterServerClient,
    name: str,
    required_components: list[str],
    workspace: DagsterWorkspace,
):
    try:
        response = vulkan_dagster_client.install_workspace(
            name=name, required_components=required_components
        )
    except Exception as e:
        workspace.status = DagsterWorkspaceStatus.INSTALL_FAILED
        db.commit()
        raise e

    workspace.status = DagsterWorkspaceStatus.OK
    db.commit()

    response_data = response.json()
    return response_data["graph"]


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
    group_by_status: bool = False,
    db: Session = Depends(get_db),
):
    start_date, end_date = _validate_date_range(start_date, end_date)

    date_clause = F.DATE(Run.created_at).label("date")
    groupers = []
    if group_by_status:
        groupers.append(Run.status.label("status"))

    policy_versions = (
        db.query(PolicyVersion.policy_version_id).filter_by(policy_id=policy_id).all()
    )
    policy_version_ids = [v.policy_version_id for v in policy_versions]

    query = (
        db.query(
            date_clause,
            F.count(Run.run_id).label("count"),
            *groupers,
        )
        .filter(
            (Run.policy_version_id.in_(policy_version_ids))
            & (Run.created_at >= start_date)
            & (F.DATE(Run.created_at) <= end_date)
        )
        .group_by(date_clause, *groupers)
    )
    df = pd.read_sql(query.statement, query.session.bind)
    if len(groupers) > 0:
        df = df.pivot(
            index="date", values="count", columns=[c.name for c in groupers]
        ).reset_index()

    return df.to_dict(orient="records")
