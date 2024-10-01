import json
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import launch_run
from vulkan_server.db import (
    Component,
    ComponentVersion,
    ComponentVersionDependency,
    Policy,
    PolicyVersion,
    Run,
    get_db,
)
from vulkan_server.logger import init_logger

logger = init_logger("policyVersions")
router = APIRouter(
    prefix="/policyVersions",
    tags=["policyVersions"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{policy_version_id}", response_model=schemas.PolicyVersion)
def get_policy_version(
    policy_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy_version_id, project_id=project_id)
        .first()
    )
    if policy_version is None:
        return Response(status_code=204)
    return policy_version


@router.post("/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: str,
    execution_config_str: Annotated[str, Body(embed=True)],
    config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
):
    try:
        execution_config = json.loads(execution_config_str)
    except Exception as e:
        HTTPException(status_code=400, detail=e)

    version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy_version_id, project_id=project_id)
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)

    run, error_msg = launch_run(
        dagster_client=dagster_client,
        server_url=config.server_url,
        execution_config=execution_config,
        policy_version_id=version.policy_version_id,
        version_name=definitions.version_name(
            version.policy_id, version.policy_version_id
        ),
        db=db,
        project_id=project_id,
    )
    if run.status == RunStatus.FAILURE:
        raise HTTPException(
            status_code=500,
            detail=f"Error triggering job: {error_msg}",
        )
    return {"policy_id": version.policy_id, "run_id": run.run_id}


@router.get("/{policy_version_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy_version(policy_version_id: str, db: Session = Depends(get_db)):
    runs = db.query(Run).filter_by(policy_version_id=policy_version_id).all()
    if len(runs) == 0:
        return Response(status_code=204)
    return runs


@router.get(
    "/{policy_version_id}/components",
    response_model=list[schemas.ComponentVersionDependencyExpanded],
)
def list_dependencies_by_policy_version(
    policy_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy_version_id, project_id=project_id)
        .first()
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
            msg = (
                f"Component version {use.component_version_id} not found, "
                f"but used by policy version {policy_version_id}"
            )
            raise HTTPException(status_code=500, detail=msg)

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
