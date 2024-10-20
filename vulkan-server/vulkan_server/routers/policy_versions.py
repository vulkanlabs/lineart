import json
from typing import Annotated

import requests
from fastapi import APIRouter, Body, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.launch_run import create_run
from vulkan_server.dagster.trigger_run import update_repository
from vulkan_server.db import (
    Component,
    ComponentVersion,
    ComponentVersionDependency,
    ConfigurationValue,
    DagsterWorkspace,
    Policy,
    PolicyVersion,
    Run,
    get_db,
)
from vulkan_server.exceptions import VulkanServerException
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


@router.delete("/{policy_version_id}")
def delete_policy_version(
    policy_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    dagster_client=Depends(get_dagster_client),
):
    # TODO: ensure this function can only be executed by ADMIN level users
    policy_version = (
        db.query(PolicyVersion)
        .filter_by(policy_version_id=policy_version_id, project_id=project_id)
        .first()
    )
    if policy_version is None or policy_version.archived:
        msg = f"Tried to delete non-existent policy version {policy_version_id}"
        raise HTTPException(status_code=404, detail=msg)

    policy = (
        db.query(Policy)
        .filter_by(policy_id=policy_version.policy_id, project_id=project_id)
        .first()
    )
    if policy.active_policy_version_id == policy_version.policy_version_id:
        msg = f"Cannot delete the active version of a policy ({policy.policy_id})"
        raise HTTPException(status_code=400, detail=msg)

    workspace = (
        db.query(DagsterWorkspace)
        .filter_by(policy_version_id=policy_version_id)
        .first()
    )

    name = definitions.version_name(policy_version.policy_id, policy_version_id)
    server_url = server_config.vulkan_dagster_server_url
    response = requests.post(
        f"{server_url}/workspaces/delete",
        json={"project_id": project_id, "name": name},
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Error deleting policy version {policy_version_id}: "
                f"{response.content}"
            ),
        )
    update_repository(dagster_client)

    db.delete(workspace)
    policy_version.archived = True
    db.commit()

    logger.info(f"Deleted policy version {policy_version_id}")
    return {"policy_version_id": policy_version_id}


@router.post("/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: str,
    input_data: Annotated[str, Body(embed=True)],
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    dagster_client=Depends(get_dagster_client),
):
    try:
        input_data_obj = json.loads(input_data)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "INVALID_INPUT_DATA",
                "msg": f"Invalid input data: {str(e)}",
            },
        )

    try:
        run = create_run(
            db=db,
            dagster_client=dagster_client,
            server_url=server_config.server_url,
            policy_version_id=policy_version_id,
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

    return {"policy_version_id": policy_version_id, "run_id": run.run_id}


@router.get(
    "/{policy_version_id}/variables",
    response_model=list[schemas.ConfigurationVariables],
)
def list_config_variables(
    policy_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
            project_id=project_id,
            archived=False,
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)

    required_variables = version.variables
    variables = (
        db.query(ConfigurationValue)
        .filter_by(policy_version_id=policy_version_id)
        .all()
    )

    variable_map = {v.key: v for v in variables}
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
    variables: Annotated[list[schemas.ConfigurationVariablesBase], Body(embed=True)],
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    version = (
        db.query(PolicyVersion)
        .filter_by(
            policy_version_id=policy_version_id,
            project_id=project_id,
            archived=False,
        )
        .first()
    )
    if version is None:
        msg = f"Policy version {policy_version_id} not found"
        raise HTTPException(status_code=404, detail=msg)

    for key, value in variables.items():
        config_value = (
            db.query(ConfigurationValue)
            .filter_by(policy_version_id=policy_version_id, key=key)
            .first()
        )
        if config_value is None:
            config_value = ConfigurationValue(
                policy_version_id=policy_version_id, key=key, value=value
            )
            db.add(config_value)
        else:
            config_value.value = value

    db.commit()
    return {"policy_version_id": policy_version_id, "variables": variables}


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
