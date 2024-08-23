import json
from typing import Annotated, Optional

import requests
from fastapi import Body, Depends, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_server import definitions, routers, schemas
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import launch_run
from vulkan_server.dagster.trigger_run import update_repository
from vulkan_server.db import (
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
    get_db,
)
from vulkan_server.logger import init_logger

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
app.include_router(routers.policies.router)


logger = init_logger("vulkan_server")


@app.post("/policyVersions/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: int,
    execution_config_str: Annotated[str, Body(embed=True)],
    config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
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

    run = launch_run(
        dagster_client=dagster_client,
        server_url=config.server_url,
        execution_config=execution_config,
        policy_version_id=version.policy_version_id,
        version_name=definitions.version_name(
            version.policy_id, version.policy_version_id
        ),
        db=db,
    )
    if run is None:
        raise HTTPException(status_code=500, detail="Error triggering job")
    return {"policy_id": version.policy_id, "run_id": run.run_id}


@app.post("/policies/{policy_id}/versions")
def create_policy_version(
    policy_id: int,
    config: schemas.PolicyVersionCreate,
    dependencies: Annotated[Optional[list[str]], Body()] = None,
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

        version_name = definitions.version_name(policy_id, version.policy_version_id)
        try:
            graph = _create_policy_version_workspace(
                db=db,
                server_url=server_config.vulkan_dagster_server_url,
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
def create_component_version(
    component_id: int,
    component_config: schemas.ComponentVersionBase,
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
):
    try:
        logger.info(f"config: {server_config.vulkan_dagster_server_url}, {server_config.server_url}")
        server_url = f"{server_config.vulkan_dagster_server_url}/components"
        # TODO: add input and output schemas and handle them in the endpoint
        response = requests.post(
            server_url,
            data={
                "alias": component_config.alias,
                "repository": component_config.repository,
            },
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to create component: {response.status_code}")
    except Exception as e:
        msg = f"Failed to create component {component_config.alias}"
        logger.error(msg)
        raise HTTPException(status_code=500, detail=str(e))

    with DBSession() as db:
        args = {"component_id": component_id, **component_config.model_dump()}
        component = ComponentVersion(**args)
        db.add(component)
        db.commit()
        logger.info(f"Creating component {component_config.alias}")

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
