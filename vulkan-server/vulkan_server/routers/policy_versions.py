"""
Policy version management router.

Handles HTTP endpoints for policy version operations. All business logic
is delegated to PolicyVersionService.
"""

import datetime
from typing import Annotated

from fastapi import APIRouter, Body, Depends, HTTPException, Response
from vulkan_engine import schemas
from vulkan_engine.dagster.launch_run import (
    MAX_POLLING_TIMEOUT_MS,
    MIN_POLLING_INTERVAL_MS,
    DagsterRunLauncher,
    get_dagster_launcher,
)
from vulkan_engine.dagster.service_client import (
    VulkanDagsterServiceClient,
    get_dagster_service_client,
)
from vulkan_engine.exceptions import (
    DataSourceNotFoundException,
    InvalidDataSourceException,
    PolicyNotFoundException,
    PolicyVersionInUseException,
    PolicyVersionNotFoundException,
)
from vulkan_engine.services import PolicyVersionService
from vulkan_engine.services.dependencies import get_service_dependencies

router = APIRouter(
    prefix="/policy-versions",
    tags=["policy-versions"],
    responses={404: {"description": "Not found"}},
)


def get_policy_version_service(
    dagster_service_client: VulkanDagsterServiceClient = Depends(
        get_dagster_service_client
    ),
    launcher: DagsterRunLauncher = Depends(get_dagster_launcher),
    deps=Depends(get_service_dependencies),
) -> PolicyVersionService:
    """Get PolicyVersionService instance with dependencies."""
    db, logger = deps
    return PolicyVersionService(
        db=db,
        dagster_service_client=dagster_service_client,
        launcher=launcher,
        logger=logger,
    )


@router.post("", response_model=schemas.PolicyVersion)
def create_policy_version(
    config: schemas.PolicyVersionCreate,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Create a new policy version."""
    try:
        return service.create_policy_version(config)
    except PolicyNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{policy_version_id}", response_model=schemas.PolicyVersion)
def get_policy_version(
    policy_version_id: str,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Get a policy version by ID."""
    version = service.get_policy_version(policy_version_id)
    if not version:
        return Response(status_code=204)
    return version


@router.get("", response_model=list[schemas.PolicyVersion])
def list_policy_versions(
    policy_id: str | None = None,
    archived: bool = False,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """List policy versions with optional filtering."""
    versions = service.list_policy_versions(policy_id, archived)
    if not versions:
        return Response(status_code=204)
    return versions


@router.put("/{policy_version_id}", response_model=schemas.PolicyVersion)
def update_policy_version(
    policy_version_id: str,
    config: schemas.PolicyVersionBase,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Update a policy version."""
    try:
        return service.update_policy_version(policy_version_id, config)
    except PolicyVersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})
    except InvalidDataSourceException as e:
        raise HTTPException(status_code=400, detail={"msg": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"msg": str(e)})


@router.delete("/{policy_version_id}")
def delete_policy_version(
    policy_version_id: str,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Delete (archive) a policy version."""
    try:
        service.delete_policy_version(policy_version_id)
        return {"policy_version_id": policy_version_id}
    except PolicyVersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PolicyVersionInUseException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_version_id}/runs")
def create_run_by_policy_version(
    policy_version_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Create a run for a policy version."""
    try:
        return service.create_run(policy_version_id, input_data, config_variables)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{policy_version_id}/run", response_model=schemas.RunResult)
async def run_workflow(
    policy_version_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    polling_interval_ms: int = MIN_POLLING_INTERVAL_MS,
    polling_timeout_ms: int = MAX_POLLING_TIMEOUT_MS,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Execute a workflow and wait for results."""
    try:
        return await service.run_workflow(
            policy_version_id,
            input_data,
            config_variables,
            polling_interval_ms,
            polling_timeout_ms,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/{policy_version_id}/variables",
    response_model=list[schemas.ConfigurationVariables],
)
def list_config_variables(
    policy_version_id: str,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """List configuration variables for a policy version."""
    try:
        return service.list_configuration_variables(policy_version_id)
    except PolicyVersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.put("/{policy_version_id}/variables")
def set_config_variables(
    policy_version_id: str,
    desired_variables: Annotated[list[schemas.ConfigurationVariablesBase], Body()],
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """Set configuration variables for a policy version."""
    try:
        return service.set_configuration_variables(policy_version_id, desired_variables)
    except PolicyVersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{policy_version_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy_version(
    policy_version_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """List runs for a policy version."""
    runs = service.list_runs_by_policy_version(policy_version_id, start_date, end_date)
    if not runs:
        return Response(status_code=204)
    return runs


@router.get(
    "/{policy_version_id}/data-sources",
    response_model=list[schemas.DataSourceReference],
)
def list_data_sources_by_policy_version(
    policy_version_id: str,
    service: PolicyVersionService = Depends(get_policy_version_service),
):
    """List data sources used by a policy version."""
    try:
        data_sources = service.list_data_sources_by_policy_version(policy_version_id)
        if not data_sources:
            return Response(status_code=204)
        return data_sources
    except PolicyVersionNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
