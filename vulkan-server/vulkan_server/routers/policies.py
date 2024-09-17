import datetime
import json
from typing import Annotated, Any

import pandas as pd
import requests
from fastapi import APIRouter, Body, Depends, Header, HTTPException, Response
from sqlalchemy import func as F
from sqlalchemy.orm import Session

from vulkan_server import definitions, schemas
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import launch_run
from vulkan_server.dagster.trigger_run import update_repository
from vulkan_server.db import (
    ComponentVersion,
    ComponentVersionDependency,
    DagsterWorkspace,
    DagsterWorkspaceStatus,
    DBSession,
    Policy,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    User,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("policies")
router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses={404: {"description": "Not found"}},
)


def get_user_id(
    x_user_id: Annotated[str, Header()],
    db: Session = Depends(get_db),
) -> str:
    if x_user_id is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    user = db.query(User).filter_by(user_auth_id=x_user_id).first()
    if user is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve user. Contact the administrator.",
        )
    return user.user_id


@router.get("/", response_model=list[schemas.Policy])
def list_policies(
    user_id=Depends(get_user_id),
    db: Session = Depends(get_db),
):
    policies = db.query(Policy).filter_by(owner_id=user_id).all()
    if len(policies) == 0:
        return Response(status_code=204)
    return policies


# TODO: Use this as the model for authenticating routes
@router.post("/")
def create_policy(
    config: schemas.PolicyBase,
    user_id=Depends(get_user_id),
    db: Session = Depends(get_db),
):
    policy = Policy(owner_id=user_id, **config.model_dump())
    db.add(policy)
    db.commit()
    logger.info(f"Policy {config.name} created")
    return {"policy_id": policy.policy_id, "name": policy.name}


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(policy_id, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter_by(policy_id=policy_id).first()
    if policy is None:
        return Response(status_code=204)
    return policy


@router.put("/{policy_id}")
def update_policy(
    policy_id: int,
    config: schemas.PolicyUpdate,
):
    with DBSession() as db:
        policy = db.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to update non-existent policy {policy_id}"
            raise HTTPException(status_code=400, detail=msg)

        if (
            config.active_policy_version_id is not None
            and config.active_policy_version_id != policy.active_policy_version_id
        ):
            policy_version = (
                db.query(PolicyVersion)
                .filter_by(policy_version_id=config.active_policy_version_id)
                .first()
            )
            if policy_version is None:
                msg = f"Tried to use non-existent version {config.active_policy_version_id} for policy {policy_id}"
                raise HTTPException(status_code=400, detail=msg)

            if policy_version.status != PolicyVersionStatus.VALID:
                msg = f"Tried to use invalid version {config.active_policy_version_id} for policy {policy_id}"
                raise HTTPException(status_code=400, detail=msg)

            policy.active_policy_version_id = config.active_policy_version_id

        if config.name is not None and config.name != policy.name:
            policy.name = config.name
        if config.description is not None and config.description != policy.description:
            policy.description = config.description

        db.commit()
        msg = f"Policy {policy_id} updated: active version set to {config.active_policy_version_id}"
        logger.info(msg)
        return {
            "policy_id": policy.policy_id,
            "active_policy_version_id": policy.active_policy_version_id,
        }


@router.get(
    "/{policy_id}/versions",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = (
        db.query(PolicyVersion)
        .filter_by(
            policy_id=policy_id,
            status=PolicyVersionStatus.VALID,
        )
        .all()
    )
    if len(policy_versions) == 0:
        return Response(status_code=204)
    return policy_versions


@router.get("/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = db.query(PolicyVersion).filter_by(policy_id=policy_id).all()
    policy_version_ids = [v.policy_version_id for v in policy_versions]
    runs = db.query(Run).filter(Run.policy_version_id.in_(policy_version_ids)).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.post("/{policy_id}/runs")
def create_run_by_policy(
    policy_id: int,
    execution_config_str: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        HTTPException(status_code=400, detail=e)

    policy = db.query(Policy).filter_by(policy_id=policy_id).first()
    if policy is None:
        raise HTTPException(status_code=400, detail=f"Policy {policy_id} not found")
    if policy.active_policy_version_id is None:
        raise HTTPException(
            status_code=400,
            detail=f"Policy {policy_id} has no active version",
        )

    version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy.active_policy_version_id)
        .first()
    )

    run = launch_run(
        dagster_client=dagster_client,
        server_url=server_config.server_url,
        execution_config=execution_config,
        policy_version_id=version.policy_version_id,
        version_name=definitions.version_name(
            version.policy_id, version.policy_version_id
        ),
        db=db,
    )
    if run is None:
        raise HTTPException(status_code=500, detail="Failed to launch run")

    return {"policy_id": policy.policy_id, "run_id": run.run_id}


@router.post("/{policy_id}/versions")
def create_policy_version(
    policy_id: int,
    config: schemas.PolicyVersionCreate,
    dagster_client=Depends(get_dagster_client),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    logger.info(f"Creating policy version for policy {policy_id}")
    if config.alias is None:
        # We can use the repo version as an easy alias or generate one.
        # This should ideally be a commit hash or similar, indicating a
        # unique version of the code.
        config.alias = config.repository_version

    with DBSession() as db:
        policy = db.query(Policy).filter_by(policy_id=policy_id).first()
        if policy is None:
            msg = f"Tried to create a version for non-existent policy {policy_id}"
            raise HTTPException(status_code=400, detail=msg)

        version = PolicyVersion(
            policy_id=policy_id,
            alias=config.alias,
            repository=config.repository,
            repository_version=config.repository_version,
            status=PolicyVersionStatus.INVALID,
        )
        db.add(version)
        db.commit()

        version_name = definitions.version_name(policy_id, version.policy_version_id)
        try:
            graph, required_components = _create_policy_version_workspace(
                db=db,
                server_url=server_config.vulkan_dagster_server_url,
                policy_version_id=version.policy_version_id,
                name=version_name,
                repository=config.repository,
            )

            if required_components:
                matched = (
                    db.query(ComponentVersion)
                    .filter(ComponentVersion.alias.in_(required_components))
                    .all()
                )
                missing = set(required_components) - set([m.alias for m in matched])
                if missing:
                    msg = f"Missing components: {missing}"
                    raise HTTPException(status_code=400, detail=msg)

                for m in matched:
                    dependency = ComponentVersionDependency(
                        component_version_id=m.component_version_id,
                        policy_version_id=version.policy_version_id,
                    )
                    db.add(dependency)

        except Exception as e:
            msg = f"Failed to create workspace for policy {policy_id} version {config.alias}"
            logger.error(msg)
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)
        finally:
            db.commit()

        msg = f"Creating version {version.policy_version_id} ({config.alias}) for policy {policy_id}"
        logger.info(msg)

        loaded_repos = update_repository(dagster_client)
        if loaded_repos.get(version_name, False) is False:
            msg = f"Failed to load repository {version_name}"
            logger.error(msg)
            logger.error(f"Repository load status: {loaded_repos}")
            raise HTTPException(status_code=500, detail=msg)

        version.status = PolicyVersionStatus.VALID
        version.graph_definition = json.dumps(graph)
        db.commit()

        msg = f"Policy version {config.alias} created for policy {policy_id} with status {version.status}"
        logger.info(msg)

        return {
            "policy_id": policy_id,
            "policy_version_id": version.policy_version_id,
            "alias": version.alias,
            "status": version.status.value,
        }


def _create_policy_version_workspace(
    db: Session,
    server_url: str,
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

    server_url = f"{server_url}/workspaces"
    response = requests.post(
        server_url,
        json={"name": name, "repository": repository},
    )
    status_code = response.status_code
    if status_code != 200:
        workspace.status = DagsterWorkspaceStatus.CREATION_FAILED
        db.commit()
        try:
            error_msg = response.json()["message"]
        except requests.exceptions.JSONDecodeError:
            error_msg = f"Status code: {status_code}"
        raise ValueError(f"Failed to create workspace: {error_msg}")

    response_data = response.json()
    workspace_path = response_data["workspace_path"]
    workspace.workspace_path = workspace_path
    workspace.status = DagsterWorkspaceStatus.OK
    db.commit()

    return response_data["graph"], response_data["required_components"]


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
    policy_id: int,
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
    policy_id: int,
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
    policy_id: int,
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
