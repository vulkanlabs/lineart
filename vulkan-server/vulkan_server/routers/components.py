import json
from itertools import chain

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from vulkan_public.exceptions import (
    UNHANDLED_ERROR_NAME,
    DataSourceNotFoundException,
    VulkanInternalException,
)
from vulkan_public.spec.component import component_version_alias

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import (
    Component,
    ComponentDataDependency,
    ComponentVersion,
    ComponentVersionDependency,
    DataSource,
    Policy,
    PolicyVersion,
    get_db,
)
from vulkan_server.exceptions import ExceptionHandler
from vulkan_server.logger import init_logger
from vulkan_server.services import (
    ResolutionServiceClient,
    VulkanDagsterServerClient,
    get_dagster_service_client,
    get_resolution_service_client,
)

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
    component = (
        db.query(Component)
        .filter_by(name=config.name, project_id=project_id, archived=False)
        .first()
    )
    if component is not None:
        raise HTTPException(status_code=409, detail="Component already exists")

    new_component = Component(project_id=project_id, **config.model_dump())
    db.add(new_component)
    db.commit()
    logger.info(f"Created component {config.name}")
    return new_component


@router.get("/", response_model=list[schemas.Component])
def list_components(
    project_id: str = Depends(get_project_id),
    include_archived: bool = False,
    db: Session = Depends(get_db),
):
    filters = dict(project_id=project_id)
    if not include_archived:
        filters["archived"] = False

    components = db.query(Component).filter_by(**filters).all()
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


@router.delete("/{component_id}")
def delete_component(
    component_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    component = (
        db.query(Component)
        .filter_by(component_id=component_id, project_id=project_id)
        .first()
    )
    if component is None or component.archived:
        msg = f"Tried to delete non-existent component {component_id}"
        raise HTTPException(status_code=404, detail=msg)

    component_versions = (
        db.query(ComponentVersion)
        .filter_by(component_id=component_id, project_id=project_id, archived=False)
        .all()
    )
    if len(component_versions) > 0:
        msg = f"Component {component_id} has associated versions, delete them first"
        raise HTTPException(status_code=400, detail=msg)

    component.archived = True
    db.commit()
    logger.info(f"Deleted component {component_id}")
    return {"component_id": component_id}


@router.post("/{component_id}/versions")
def create_component_version(
    component_id: str,
    component_config: schemas.ComponentVersionCreate,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
    dagster_launcher_client: VulkanDagsterServerClient = Depends(
        get_dagster_service_client
    ),
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
        # TODO: add input and output schemas and handle them in the endpoint
        response = resolution_service.create_component_version(
            alias, component_config.repository
        )
        data = response.json()
        variables = data.get("config_variables", [])
        data_sources = data.get("data_sources", [])

        version = ComponentVersion(
            alias=alias,
            component_id=component_id,
            project_id=project_id,
            input_schema=str(data["input_schema"]),
            instance_params_schema=str(data["instance_params_schema"]),
            node_definitions=json.dumps(data["node_definitions"]),
            repository=component_config.repository,
        )
        db.add(version)

        if data_sources:
            added_sources = _add_data_source_dependencies(db, version, data_sources)
            inner_variables = [ds.variables for ds in added_sources if ds.variables]
            variables += list(chain.from_iterable(inner_variables))

        if variables:
            version.variables = list(set(variables))

        # dagster_launcher_client.create_component_version(
        #     alias, component_config.repository
        # )
        db.commit()
    except Exception as e:
        # Remove leftover resources from failed creation
        resolution_service.delete_component_version(alias)
        # dagster_launcher_client.delete_component_version(alias)

        if isinstance(e, VulkanInternalException):
            handler.raise_exception(400, e.__class__.__name__, str(e), e.metadata)
        handler.raise_exception(500, UNHANDLED_ERROR_NAME, str(e))

    return {"component_version_id": version.component_version_id}


def _add_data_source_dependencies(
    db: Session, component_version: ComponentVersion, data_sources: list[str]
) -> list[DataSource]:
    matched = (
        db.query(DataSource)
        .filter(
            DataSource.name.in_(data_sources),
            DataSource.project_id == component_version.project_id,
            DataSource.archived == False,  # noqa: E712
        )
        .all()
    )
    missing = list(set(data_sources) - {m.name for m in matched})
    if missing:
        raise DataSourceNotFoundException(
            msg=f"The following data sources are not defined: {missing}",
            metadata={"data_sources": missing},
        )

    for m in matched:
        dependency = ComponentDataDependency(
            data_source_id=m.data_source_id,
            component_version_id=component_version.component_version_id,
        )
        db.add(dependency)

    return matched


@router.get(
    "/{component_id}/versions",
    response_model=list[schemas.ComponentVersion],
)
def list_component_versions(
    component_id: str,
    include_archived: bool = False,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
):
    filters = dict(component_id=component_id, project_id=project_id)
    if not include_archived:
        filters["archived"] = False

    versions = db.query(ComponentVersion).filter_by(**filters).all()
    if len(versions) == 0:
        return Response(status_code=204)
    return versions


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
