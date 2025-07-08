"""
Run management router.

Handles HTTP endpoints for run operations. All business logic
is delegated to RunService.
"""

from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException
from vulkan_engine import schemas
from vulkan_engine.dagster.launch_run import DagsterRunLauncher, get_dagster_launcher
from vulkan_engine.exceptions import RunNotFoundException
from vulkan_engine.services import RunService
from vulkan_engine.services.dependencies import get_service_dependencies

router = APIRouter(
    prefix="/runs",
    tags=["runs"],
    responses={404: {"description": "Not found"}},
)


def get_run_service(
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
    deps=Depends(get_service_dependencies),
) -> RunService:
    """Get RunService instance with dependencies."""
    db, logger = deps
    return RunService(db=db, launcher=launcher, logger=logger)


@router.get("/{run_id}/data", response_model=schemas.RunData)
def get_run_data(
    run_id: str,
    service: RunService = Depends(get_run_service),
):
    """Get run data including step outputs and metadata."""
    try:
        return service.get_run_data(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        # Handle unpickling errors
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{run_id}/logs", response_model=schemas.RunLogs)
def get_run_logs(
    run_id: str,
    service: RunService = Depends(get_run_service),
):
    """Get logs for a run."""
    try:
        return service.get_run_logs(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{run_id}", response_model=schemas.Run)
def get_run(
    run_id: str,
    service: RunService = Depends(get_run_service),
):
    """Get run details."""
    try:
        return service.get_run(run_id)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}/metadata")
def publish_metadata(
    run_id: str,
    config: schemas.StepMetadataBase,
    service: RunService = Depends(get_run_service),
):
    """Publish metadata for a run step."""
    try:
        return service.publish_step_metadata(run_id, config)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: str,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    metadata: Annotated[dict[str, Any] | None, Body()] = None,
    service: RunService = Depends(get_run_service),
):
    """Update run status and optionally trigger shadow runs."""
    try:
        return service.update_run_status(run_id, status, result, metadata)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
