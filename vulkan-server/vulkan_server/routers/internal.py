"""Internal API endpoints for service-to-service communication."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException
from vulkan_engine import schemas
from vulkan_engine.exceptions import (
    DataBrokerException,
    DataBrokerRequestException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
    RunNotFoundException,
)
from vulkan_engine.services import DataSourceService, PolicyVersionService
from vulkan_engine.services.run_orchestration import (
    MAX_POLLING_TIMEOUT_MS,
    MIN_POLLING_INTERVAL_MS,
    RunOrchestrationService,
)

from vulkan_server.dependencies import (
    get_data_source_service,
    get_policy_version_service,
    get_run_orchestration_service,
)

router = APIRouter(
    prefix="/internal",
    tags=["internal"],
    responses={404: {"description": "Not found"}},
)


@router.post("/run-version-sync", response_model=schemas.RunResult)
async def run_version_sync(
    policy_version_id: Annotated[UUID, Body()],
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    polling_interval_ms: int = MIN_POLLING_INTERVAL_MS,
    polling_timeout_ms: int = MAX_POLLING_TIMEOUT_MS,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Execute a workflow and wait for results."""
    try:
        return await service.run_workflow(
            str(policy_version_id),
            input_data,
            config_variables,
            polling_interval_ms,
            polling_timeout_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/data-broker", response_model=schemas.DataBrokerResponse)
def request_data_from_broker(
    request: schemas.DataBrokerRequest,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Request data through the data broker."""
    try:
        return service.request_data_from_broker(request)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDataSourceException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except DataBrokerRequestException as e:
        raise HTTPException(status_code=502, detail=str(e))
    except DataBrokerException as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{run_id}/metadata")
def publish_metadata(
    run_id: UUID,
    config: schemas.StepMetadataBase,
    service: RunOrchestrationService = Depends(get_run_orchestration_service),
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


@router.put("/runs/{run_id}", response_model=schemas.Run)
def update_run(
    run_id: UUID,
    status: Annotated[str, Body()],
    result: Annotated[str, Body()],
    metadata: Annotated[dict[str, Any] | None, Body()] = None,
    service: RunOrchestrationService = Depends(get_run_orchestration_service),
):
    """Update run status and optionally trigger shadow runs."""
    try:
        return service.update_run_status(run_id, status, result, metadata)
    except RunNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
