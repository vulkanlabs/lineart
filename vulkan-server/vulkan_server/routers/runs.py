"""
Run management router.

Handles HTTP endpoints for run operations. All business logic
is delegated to RunService.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from vulkan_engine import schemas
from vulkan_engine.exceptions import RunNotFoundException
from vulkan_engine.services.run_query import RunQueryService

from vulkan_server.dependencies import get_run_query_service

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    responses={404: {"description": "Not found"}},
)


@router.get("/{run_id}/data", response_model=schemas.RunData)
async def get_run_data(
    run_id: str,
    service: Annotated[RunQueryService, Depends(get_run_query_service)],
):
    """Get run data including step outputs and metadata."""
    try:
        return await service.get_run_data(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Handle unpickling errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/logs", response_model=schemas.RunLogs)
async def get_run_logs(
    run_id: str,
    service: Annotated[RunQueryService, Depends(get_run_query_service)],
):
    """Get logs for a run."""
    try:
        return await service.get_run_logs(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{run_id}", response_model=schemas.Run)
async def get_run(
    run_id: str,
    service: Annotated[RunQueryService, Depends(get_run_query_service)],
):
    """Get run details."""
    try:
        return await service.get_run(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
