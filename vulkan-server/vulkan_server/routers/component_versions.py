from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from vulkan_server import schemas
from vulkan_server.auth import get_project_id
from vulkan_server.db import (
    ComponentDataDependency,
    ComponentVersion,
    ComponentVersionDependency,
    DataSource,
    PolicyVersion,
    get_db,
)
from vulkan_server.logger import init_logger
from vulkan_server.services.resolution import (
    ResolutionServiceClient,
    get_resolution_service_client,
)

logger = init_logger("component-versions")
router = APIRouter(
    prefix="/component-versions",
    tags=["component-versions"],
    responses={404: {"description": "Not found"}},
)


@router.get(
    "/{component_version_id}",
    response_model=schemas.ComponentVersion,
)
def get_component_version(
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


@router.delete("/{component_version_id}")
def delete_component_version(
    component_version_id: str,
    project_id: str = Depends(get_project_id),
    db: Session = Depends(get_db),
    resolution_service: ResolutionServiceClient = Depends(
        get_resolution_service_client
    ),
):
    # TODO: ensure this function can only be executed by ADMIN level users
    component_version = (
        db.query(ComponentVersion)
        .filter_by(component_version_id=component_version_id, project_id=project_id)
        .first()
    )
    if component_version is None or component_version.archived:
        msg = f"Tried to delete non-existent component version {component_version_id}"
        raise HTTPException(status_code=404, detail=msg)

    component_version_uses = (
        db.query(ComponentVersionDependency, PolicyVersion)
        .join(PolicyVersion)
        .filter(
            ComponentVersionDependency.component_version_id == component_version_id,
            PolicyVersion.archived == False,  # noqa: E712
        )
        .all()
    )
    if len(component_version_uses) > 0:
        msg = (
            f"Component version {component_version_id} is used by one or "
            "more policy versions"
        )
        raise HTTPException(status_code=400, detail=msg)

    try:
        _ = resolution_service.delete_component_version(component_version.alias)
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting component version {component_version_id}",
        )

    component_version.archived = True
    db.commit()
    logger.info(f"Deleted component version {component_version_id}")
    return {"component_version_id": component_version_id}


@router.get(
    "/{component_version_id}/data-sources",
    response_model=list[schemas.DataSourceReference],
)
def list_data_sources_by_component_version(
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
        raise HTTPException(status_code=404, detail="Policy version not found")

    data_source_uses = (
        db.query(ComponentDataDependency)
        .filter_by(component_version_id=component_version_id)
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
