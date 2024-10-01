import json

import requests
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan.exceptions import (
    UNHANDLED_ERROR_NAME,
    VULKAN_INTERNAL_EXCEPTIONS,
    VulkanInternalException,
)
from vulkan.spec.component import component_version_alias

from vulkan_server import definitions, schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import (
    Component,
    ComponentVersion,
    ComponentVersionDependency,
    Policy,
    PolicyVersion,
    get_db,
)
from vulkan_server.exceptions import ExceptionHandler
from vulkan_server.logger import init_logger

logger = init_logger("components")
router = APIRouter(
    prefix="/components",
    tags=["components"],
    responses={404: {"description": "Not found"}},
)


# TODO: check if the python modules names are unique
#       This can be validated on component creation.
@router.post("/", response_model=schemas.Component)
def create_component(
    config: schemas.ComponentBase,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    component = db.query(Component).filter_by(name=config.name).first()
    if component is not None:
        raise HTTPException(status_code=409, detail="Component already exists")

    new_component = Component(project_id=project_id, **config.model_dump())
    db.add(new_component)
    db.commit()
    logger.info(f"Creating component {config.name}")
    return new_component


@router.get("/", response_model=list[schemas.Component])
def list_components(
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    components = db.query(Component).filter_by(project_id=project_id).all()
    if len(components) == 0:
        return Response(status_code=204)
    return components


@router.get("/{component_id}", response_model=schemas.Component)
def get_component(
    component_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    component = (
        db.query(Component)
        .filter_by(component_id=component_id, project_id=project_id)
        .first()
    )
    if component is None:
        return Response(status_code=404)
    return component


@router.post("/{component_id}/versions")
def create_component_version(
    component_id: str,
    component_config: schemas.ComponentVersionCreate,
    project_id: str = Depends(get_project_id),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    db: Session = Depends(get_db),
):
    component = (
        db.query(Component)
        .filter_by(component_id=component_id, project_id=project_id)
        .first()
    )
    if component is None:
        raise HTTPException(status_code=404, detail="Component not found")

    alias = component_version_alias(component.name, component_config.version_name)
    handler = ExceptionHandler(logger, f"Failed to create component version {alias}")

    try:
        logger.info(
            f"config: {server_config.vulkan_dagster_server_url}, {server_config.server_url}"
        )
        server_url = f"{server_config.vulkan_dagster_server_url}/components"
        # TODO: add input and output schemas and handle them in the endpoint
        response = requests.post(
            server_url,
            data={"alias": alias, "repository": component_config.repository},
        )
        if response.status_code != 200:
            detail = response.json().get("detail", {})
            if detail.get("error") == "VulkanInternalException":
                raise VULKAN_INTERNAL_EXCEPTIONS[detail.get("exit_status")](
                    msg=detail.get("msg")
                )
            raise Exception(detail.get("msg"))

        data = response.json()
    except VulkanInternalException as e:
        error_name = VULKAN_INTERNAL_EXCEPTIONS[e.exit_status].__name__
        handler.raise_exception(400, error_name, str(e), e.metadata)
    except Exception as e:
        handler.raise_exception(status_code=500, error=UNHANDLED_ERROR_NAME, msg=str(e))

    component = ComponentVersion(
        component_id=component_id,
        input_schema=str(data["input_schema"]),
        instance_params_schema=str(data["instance_params_schema"]),
        node_definitions=json.dumps(data["node_definitions"]),
        project_id=project_id,
        alias=alias,
        repository=component_config.repository,
    )
    db.add(component)
    db.commit()
    logger.info(f"Creating component {alias}")

    return {"status": "success"}


@router.get(
    "/{component_id}/versions",
    response_model=list[schemas.ComponentVersion],
)
def list_component_versions(
    component_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    versions = (
        db.query(ComponentVersion)
        .filter_by(component_id=component_id, project_id=project_id)
        .all()
    )
    if len(versions) == 0:
        return Response(status_code=204)
    return versions


@router.get(
    "/{component_id}/versions/{component_version_id}",
    response_model=schemas.ComponentVersion,
)
def get_component_version(
    component_id: str,
    component_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    component_version = (
        db.query(ComponentVersion)
        .filter_by(component_version_id=component_version_id, project_id=project_id)
        .first()
    )
    if component_version is None:
        return Response(status_code=404)
    return component_version


@router.get(
    "/{component_id}/usage",
    response_model=list[schemas.ComponentVersionDependencyExpanded],
)
def list_component_usage(
    component_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    component_versions = (
        db.query(ComponentVersion)
        .filter_by(component_id=component_id, project_id=project_id)
        .all()
    )
    if len(component_versions) == 0:
        return Response(status_code=204)

    usage = []
    for component_version in component_versions:
        version_usage = list_component_version_usage(
            component_version.component_version_id, project_id, db
        )
        if len(version_usage) > 0:
            usage.extend(version_usage)

    return usage


def list_component_version_usage(
    component_version_id: str, project_id: str, db: Session
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
        .filter_by(component_version_id=component_version_id, project_id=project_id)
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
