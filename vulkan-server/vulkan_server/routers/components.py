"""
Component management router.

Handles HTTP endpoints for component operations. All business logic
is delegated to ComponentService.
"""

from fastapi import APIRouter, Depends, HTTPException, Response
from vulkan_engine import schemas
from vulkan_engine.exceptions import ComponentNotFoundException
from vulkan_engine.services import ComponentService

from vulkan_server.dependencies import get_component_service

router = APIRouter(
    prefix="/components",
    tags=["components"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Component])
def list_components(
    include_archived: bool = False,
    service: ComponentService = Depends(get_component_service),
    project_id: str | None = None,
):
    """List all components."""
    components = service.list_components(
        include_archived=include_archived, project_id=project_id
    )
    if not components:
        return Response(status_code=204)
    return components


@router.post("/", response_model=schemas.Component)
def create_component(
    config: schemas.ComponentUpdate,
    service: ComponentService = Depends(get_component_service),
    project_id: str | None = None,
):
    """Create a new component."""
    return service.create_component(config, project_id=project_id)


@router.get("/{component_id}", response_model=schemas.Component)
def get_component(
    component_id: str,
    service: ComponentService = Depends(get_component_service),
    project_id: str | None = None,
):
    """Get a component by ID."""
    try:
        return service.get_component(component_id, project_id)
    except ComponentNotFoundException:
        return Response(status_code=404)


@router.put("/{component_id}", response_model=schemas.Component)
def update_component(
    component_id: str,
    config: schemas.ComponentUpdate,
    service: ComponentService = Depends(get_component_service),
    project_id: str | None = None,
):
    """Update a component."""
    try:
        return service.update_component(component_id, config, project_id=project_id)
    except ComponentNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{component_id}")
def delete_component(
    component_id: str,
    service: ComponentService = Depends(get_component_service),
    project_id: str | None = None,
):
    """Delete (archive) a component."""
    try:
        service.delete_component(component_id, project_id=project_id)
        return {"component_id": component_id}
    except ComponentNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
