import datetime
import json
import logging
import os
from typing import Annotated, Any, Optional

import pandas as pd
import requests
from dotenv import load_dotenv
from fastapi import Body, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func as F
from sqlalchemy.orm import Session

from vulkan_dagster.core.run import RunStatus
from vulkan_dagster.dagster.policy import DEFAULT_POLICY_NAME

from . import schemas
from .db import (
    Component,
    ComponentVersion,
    ComponentVersionDependency,
    DagsterWorkspace,
    DagsterWorkspaceStatus,
    DBSession,
    Policy,
    PolicyVersion,
    PolicyVersionStatus,
    Run,
    StepMetadata,
)
from .trigger_run import create_dagster_client, trigger_dagster_job, update_repository

app = FastAPI()

origins = [
    "http://127.0.0.1",
    "http://0.0.0.0",
    "http://localhost",
    "http://localhost:8080",
    "http://host.docker.internal",
    "http://host.docker.internal:8080",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)

load_dotenv()
SERVER_URL = f"http://app:{os.getenv('APP_PORT')}"
VULKAN_DAGSTER_SERVER_URL = os.getenv("VULKAN_DAGSTER_SERVER_URL")

DAGSTER_URL = "dagster"
DAGSTER_PORT = 3000
dagster_client = create_dagster_client(DAGSTER_URL, DAGSTER_PORT)
logger.info(f"Dagster client created at http://{DAGSTER_URL}:{DAGSTER_PORT}")

# TODO: Configure the maximum period of time we allow queries for.
MAX_DAYS = 30


def get_db():
    db = DBSession()
    try:
        yield db
    finally:
        db.close()


@app.get("/policies", response_model=list[schemas.Policy])
def list_policies(db: Session = Depends(get_db)):
    policies = db.query(Policy).all()
    if len(policies) == 0:
        return Response(status_code=204)
    return policies


@app.post("/policies")
def create_policy(config: schemas.PolicyBase):
    with DBSession() as db:
        policy = Policy(**config.model_dump())
        db.add(policy)
        db.commit()
        logger.info(f"Policy {config.name} created")
        return {"policy_id": policy.policy_id, "name": policy.name}


@app.get("/policies/{policy_id}", response_model=schemas.Policy)
def get_policy(policy_id, db: Session = Depends(get_db)):
    policy = db.query(Policy).filter_by(policy_id=policy_id).first()
    if policy is None:
        return Response(status_code=204)
    return policy


@app.put("/policies/{policy_id}")
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


@app.get(
    "/policies/{policy_id}/versions",
    response_model=list[schemas.PolicyVersion],
)
def list_policy_versions(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = db.query(PolicyVersion).filter_by(policy_id=policy_id).all()
    if len(policy_versions) == 0:
        return Response(status_code=204)
    return policy_versions


@app.get("/policies/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(policy_id: int, db: Session = Depends(get_db)):
    policy_versions = db.query(PolicyVersion).filter_by(policy_id=policy_id).all()
    policy_version_ids = [v.policy_version_id for v in policy_versions]
    runs = db.query(Run).filter(Run.policy_version_id.in_(policy_version_ids)).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@app.get("/policies/{policy_id}/runs/count", response_model=list[Any])
def count_runs_by_policy(
    policy_id: int,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    group_by_status: bool = False,
    db: Session = Depends(get_db),
):
    if end_date is None:
        end_date = datetime.date.today()
    if start_date is None:
        start_date = end_date - datetime.timedelta(days=30)

    active_version = db.query(Policy).filter_by(policy_id=policy_id).first()
    if active_version is None:
        raise HTTPException(status_code=400, detail=f"Policy {policy_id} not found")

    date_clause = F.DATE(Run.created_at).label("date")
    groupers = []
    if group_by_status:
        groupers.append(Run.status.label("status"))

    query = (
        db.query(
            date_clause,
            F.count(Run.run_id).label("count"),
            *groupers,
        )
        .filter(
            # TODO: Should get runs for all policy versions.
            (Run.policy_version_id == active_version.active_policy_version_id)
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


@app.post("/policies/{policy_id}/runs")
def create_run_by_policy(
    policy_id: int,
    execution_config_str: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),
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

    run = _launch_run(
        execution_config, version.policy_id, version.policy_version_id, db
    )
    return {"policy_id": policy.policy_id, "run_id": run.run_id}


@app.post("/policyVersions/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: int,
    execution_config_str: Annotated[str, Body(embed=True)],
    db: Session = Depends(get_db),
):
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        HTTPException(status_code=400, detail=e)

    version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=400, detail=msg)

    run = _launch_run(
        execution_config, version.policy_id, version.policy_version_id, db
    )
    if run is None:
        raise HTTPException(status_code=500, detail="Error triggering job")
    return {"policy_id": version.policy_id, "run_id": run.run_id}


def _launch_run(
    execution_config: dict, policy_id: int, policy_version_id: int, db: Session
):
    run = Run(policy_version_id=policy_version_id, status=RunStatus.PENDING)
    db.add(run)
    db.commit()

    dagster_run_id = _trigger_dagster_job(
        execution_config,
        policy_id,
        policy_version_id,
        run.run_id,
    )
    if dagster_run_id is None:
        run.status = RunStatus.FAILURE
        db.commit()
        return None

    run.status = RunStatus.STARTED
    run.dagster_run_id = dagster_run_id
    db.commit()
    return run


def _trigger_dagster_job(
    execution_config: dict, policy_id: int, policy_version_id: int, run_id: int
):
    # Trigger the Dagster job with Policy and Run IDs as inputs
    execution_config["resources"] = {
        "vulkan_run_config": {
            "config": {
                "run_id": run_id,
                "server_url": SERVER_URL,
            }
        }
    }
    dagster_run_id = trigger_dagster_job(
        dagster_client,
        _version_name(policy_id, policy_version_id),
        DEFAULT_POLICY_NAME,
        execution_config,
    )
    return dagster_run_id


@app.post("/policies/{policy_id}/versions")
def create_policy_version(
    policy_id: int,
    config: schemas.PolicyVersionCreate,
    dependencies: Annotated[Optional[list[str]], Body()] = None,
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
            entrypoint=config.entrypoint,
            status=PolicyVersionStatus.INVALID,
        )
        db.add(version)

        # Dependencies are added in the same transaction as the policy version
        # so we can rollback if any of them are missing.
        if dependencies:
            matched = (
                db.query(ComponentVersion)
                .filter(ComponentVersion.alias.in_(dependencies))
                .all()
            )
            missing = set(dependencies) - set([m.alias for m in matched])
            if missing:
                msg = f"Missing components: {missing}"
                raise HTTPException(status_code=400, detail=msg)

            for m in matched:
                dependency = ComponentVersionDependency(
                    component_version_id=m.component_version_id,
                    policy_version_id=version.policy_version_id,
                )
                db.add(dependency)

        db.commit()
        msg = f"Creating version {version.policy_version_id} ({config.alias}) for policy {policy_id}"
        logger.info(msg)

        version_name = _version_name(policy_id, version.policy_version_id)
        try:
            graph = _create_policy_version_workspace(
                db=db,
                server_url=VULKAN_DAGSTER_SERVER_URL,
                policy_version_id=version.policy_version_id,
                name=version_name,
                entrypoint=config.entrypoint,
                repository=config.repository,
                dependencies=dependencies,
            )
        except Exception as e:
            msg = f"Failed to create workspace for policy {policy_id} version {config.alias}"
            logger.error(msg)
            logger.error(e)
            raise HTTPException(status_code=500, detail=e)

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


def _version_name(policy_id: int, policy_version_id: int) -> str:
    return f"policy-{policy_id}-version-{policy_version_id}"


def _create_policy_version_workspace(
    db: Session,
    server_url: str,
    policy_version_id: int,
    name: str,
    entrypoint: str,
    repository: str,
    dependencies: Optional[list[str]] = None,
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
        json={
            "name": name,
            "entrypoint": entrypoint,
            "repository": repository,
            "dependencies": dependencies,
        },
    )
    status_code = response.status_code
    if status_code != 200:
        workspace.status = DagsterWorkspaceStatus.CREATION_FAILED
        db.commit()
        try:
            error_msg = response.json()["message"]
            raise ValueError(f"Failed to create workspace: {error_msg}")
        except:
            raise ValueError(f"Failed to create workspace: {status_code}")

    response_data = response.json()
    workspace_path = response_data["workspace_path"]
    workspace.workspace_path = workspace_path
    workspace.status = DagsterWorkspaceStatus.OK
    db.commit()

    return response_data["graph"]


@app.get("/policyVersions/{policy_version_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy_version(policy_version_id: int, db: Session = Depends(get_db)):
    runs = db.query(Run).filter_by(policy_version_id=policy_version_id).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@app.get(
    "/policyVersions/{policy_version_id}/components",
    response_model=list[schemas.ComponentVersionDependencyExpanded],
)
def list_dependencies_by_policy_version(
    policy_version_id: int, db: Session = Depends(get_db)
):
    policy_version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if policy_version is None:
        raise ValueError(f"Policy version {policy_version_id} not found")

    component_version_uses = (
        db.query(ComponentVersionDependency)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )
    if len(component_version_uses) == 0:
        return Response(status_code=204)

    policy = db.query(Policy).filter_by(policy_id=policy_version.policy_id).first()

    dependencies = []
    for use in component_version_uses:
        component_version = (
            db.query(ComponentVersion)
            .filter_by(component_version_id=use.component_version_id)
            .first()
        )

        if component_version is None:
            raise ValueError(f"Component version {use.component_version_id} not found")

        component = (
            db.query(Component)
            .filter_by(component_id=component_version.component_id)
            .first()
        )
        dependencies.append(
            schemas.ComponentVersionDependencyExpanded(
                component_id=component.component_id,
                component_name=component.name,
                component_version_id=component_version.component_version_id,
                component_version_alias=component_version.alias,
                policy_id=policy.policy_id,
                policy_name=policy.name,
                policy_version_id=policy_version.policy_version_id,
                policy_version_alias=policy_version.alias,
            )
        )

    return dependencies


@app.get(
    "/policyVersions/{policy_version_id}",
    response_model=schemas.PolicyVersion,
)
def get_policy_version(policy_version_id: int, db: Session = Depends(get_db)):
    policy_version = (
        db.query(PolicyVersion).filter_by(policy_version_id=policy_version_id).first()
    )
    if policy_version is None:
        return Response(status_code=204)
    return policy_version


# Podemos ter um run_policy_async e um sync
# O sync vai esperar a run terminar e retornar o status
# O async vai retornar o run_id e o status da run vai ser atualizado
# depois via uma chamada nossa para algum endpoint


@app.get("/runs/{run_id}", response_model=schemas.Run)
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")
    return run


@app.put("/runs/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: int,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    db: Session = Depends(get_db),
):
    run = db.query(Run).filter_by(run_id=run_id).first()
    if run is None:
        raise HTTPException(status_code=400, detail=f"Run {run_id} not found")

    try:
        status = RunStatus(status)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    run.status = status
    run.result = result
    db.commit()
    return run


# Add Policy metrics endpoint
# It should calculate the number of executions, average execution time,
# Distribution of run outcomes (approved, analysis, denied) and the success rate
# over time, per day.
# The user should be able to filter by policy_id, date range, and run outcome.
@app.get("/policies/{policy_id}/metrics")
def get_policy_metrics(policy_id: int):
    pass


@app.post("/runs/{run_id}/metadata")
def publish_metadata(run_id: int, config: schemas.StepMetadataBase):
    try:
        with DBSession() as db:
            args = {"run_id": run_id, **config.model_dump()}
            meta = StepMetadata(**args)
            db.add(meta)
            db.commit()
            return {"status": "success"}
    except KeyError as e:
        raise HTTPException(status_code=400, detail=e)
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)


@app.post("/components", response_model=schemas.Component)
def create_component(config: schemas.ComponentBase, db: Session = Depends(get_db)):
    component = Component(**config.model_dump())
    db.add(component)
    db.commit()
    logger.info(f"Creating component {config.name}")
    return component


@app.get("/components", response_model=list[schemas.Component])
def list_components(db: Session = Depends(get_db)):
    components = db.query(Component).all()
    if len(components) == 0:
        return Response(status_code=204)
    return components


@app.post("/components/{component_id}/versions")
def create_component_version(component_id: int, config: schemas.ComponentVersionBase):
    try:
        server_url = f"{VULKAN_DAGSTER_SERVER_URL}/components"
        # TODO: add input and output schemas and handle them in the endpoint
        response = requests.post(
            server_url,
            data={"alias": config.alias, "repository": config.repository},
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to create component: {response.status_code}")
    except Exception as e:
        msg = f"Failed to create component {config.alias}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=str(e))

    with DBSession() as db:
        args = {"component_id": component_id, **config.model_dump()}
        component = ComponentVersion(**args)
        db.add(component)
        db.commit()
        logger.info(f"Creating component {config.alias}")

    return {"status": "success"}


@app.get(
    "/components/{component_id}/versions",
    response_model=list[schemas.ComponentVersion],
)
def list_component_versions(component_id: int, db: Session = Depends(get_db)):
    versions = db.query(ComponentVersion).filter_by(component_id=component_id).all()
    if len(versions) == 0:
        return Response(status_code=204)
    return versions


@app.get(
    "/components/{component_id}/usage",
    response_model=list[schemas.ComponentVersionDependencyExpanded],
)
def list_component_usage(component_id: int, db: Session = Depends(get_db)):
    component_versions = (
        db.query(ComponentVersion).filter_by(component_id=component_id).all()
    )
    if len(component_versions) == 0:
        return Response(status_code=204)

    usage = []
    for component_version in component_versions:
        version_usage = list_component_version_usage(
            component_version.component_version_id, db
        )
        if len(version_usage) > 0:
            usage.extend(version_usage)

    return usage


def list_component_version_usage(
    component_version_id: int, db: Session = Depends(get_db)
) -> list[schemas.ComponentVersionDependencyExpanded]:
    component_version_uses = (
        db.query(ComponentVersionDependency)
        .filter_by(component_version_id=component_version_id)
        .all()
    )
    if len(component_version_uses) == 0:
        return []

    component = (
        db.query(
            ComponentVersion.component_version_id,
            ComponentVersion.alias,
            ComponentVersion.component_id,
            Component.name,
        )
        .filter_by(component_version_id=component_version_id)
        .first()
    )

    dependencies = []
    for use in component_version_uses:
        policy_version = (
            db.query(
                PolicyVersion.policy_id,
                PolicyVersion.policy_version_id,
                Policy.name.label("policy_name"),
                PolicyVersion.alias.label("policy_version_alias"),
            )
            .filter_by(policy_version_id=use.policy_version_id)
            .first()
        )

        if policy_version is None:
            raise ValueError(f"Policy version {use.policy_version_id} not found")

        dependencies.append(
            schemas.ComponentVersionDependencyExpanded(
                component_id=component.component_id,
                component_name=component.name,
                component_version_id=component.component_version_id,
                component_version_alias=component.alias,
                policy_id=policy_version.policy_id,
                policy_name=policy_version.policy_name,
                policy_version_id=policy_version.policy_version_id,
                policy_version_alias=policy_version.policy_version_alias,
            )
        )

    return dependencies
