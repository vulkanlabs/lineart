"""
Policy management router.

Handles HTTP endpoints for policy operations. All business logic
is delegated to PolicyService and AllocationService.
"""

import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response
from vulkan_engine import schemas
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
    InvalidPolicyVersionException,
    PolicyHasVersionsException,
    PolicyNotFoundException,
    PolicyVersionNotFoundException,
)
from vulkan_engine.services import (
    AllocationService,
    PolicyAnalyticsService,
    PolicyService,
)

from vulkan_server.dependencies import (
    get_allocation_service,
    get_policy_analytics_service,
    get_policy_service,
)

router = APIRouter(
    prefix="/policies",
    tags=["policies"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=list[schemas.Policy])
def list_policies(
    include_archived: bool = False,
    service: PolicyService = Depends(get_policy_service),
):
    """List all policies."""
    policies = service.list_policies(include_archived=include_archived)
    if not policies:
        return Response(status_code=204)
    return policies


@router.post("/", response_model=schemas.Policy)
def create_policy(
    config: schemas.PolicyCreate,
    service: PolicyService = Depends(get_policy_service),
):
    """Create a new policy."""
    return service.create_policy(config)


@router.get("/{policy_id}", response_model=schemas.Policy)
def get_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """Get a policy by ID."""
    try:
        return service.get_policy(policy_id)
    except PolicyNotFoundException:
        return Response(status_code=404)


@router.put("/{policy_id}", response_model=schemas.Policy)
def update_policy(
    policy_id: str,
    config: schemas.PolicyBase,
    service: PolicyService = Depends(get_policy_service),
):
    """Update a policy."""
    try:
        return service.update_policy(policy_id, config)
    except PolicyNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidAllocationStrategyException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except (PolicyVersionNotFoundException, InvalidPolicyVersionException) as e:
        # These can occur during allocation strategy validation
        raise HTTPException(
            status_code=e.status_code if hasattr(e, "status_code") else 400,
            detail=str(e),
        )


@router.delete("/{policy_id}")
def delete_policy(
    policy_id: str,
    service: PolicyService = Depends(get_policy_service),
):
    """Delete (archive) a policy."""
    try:
        service.delete_policy(policy_id)
        return {"policy_id": policy_id}
    except PolicyNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except PolicyHasVersionsException as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{policy_id}/versions", response_model=list[schemas.PolicyVersion])
def list_policy_versions_by_policy(
    policy_id: str,
    include_archived: bool = False,
    service: PolicyService = Depends(get_policy_service),
):
    """List versions for a policy."""
    versions = service.list_policy_versions(policy_id, include_archived)
    if not versions:
        return Response(status_code=204)
    return versions


@router.get("/{policy_id}/runs", response_model=list[schemas.Run])
def list_runs_by_policy(
    policy_id: str,
    start_date: Annotated[datetime.datetime | None, Query()] = None,
    end_date: Annotated[datetime.datetime | None, Query()] = None,
    service: PolicyService = Depends(get_policy_service),
):
    """List runs for a policy."""
    start_date_parsed = start_date.date() if start_date else None
    end_date_parsed = end_date.date() if end_date else None
    runs = service.list_runs_by_policy(policy_id, start_date_parsed, end_date_parsed)
    if not runs:
        return Response(status_code=204)
    return runs


@router.post("/{policy_id}/runs", response_model=schemas.RunGroupResult)
def create_run_group(
    policy_id: str,
    input_data: Annotated[dict, Body()],
    config_variables: Annotated[dict, Body(default_factory=dict)],
    service: AllocationService = Depends(get_allocation_service),
):
    """Create a run group and allocate runs."""
    try:
        return service.create_run_group(policy_id, input_data, config_variables)
    except PolicyNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidAllocationStrategyException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # Handle unexpected errors
        raise HTTPException(
            status_code=500,
            detail={
                "error": "UNHANDLED_EXCEPTION",
                "msg": f"Failed to create run group: {str(e)}",
            },
        )


@router.post("/{policy_id}/runs/duration/query", response_model=list[Any])
def run_duration_stats_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    service: PolicyAnalyticsService = Depends(get_policy_analytics_service),
):
    """Get run duration statistics for a policy."""
    return service.get_run_duration_stats(policy_id, start_date, end_date, versions)


@router.post("/{policy_id}/runs/duration/by_status/query", response_model=list[Any])
def run_duration_stats_by_policy_status(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    service: PolicyAnalyticsService = Depends(get_policy_analytics_service),
):
    """Get run duration statistics grouped by status."""
    return service.get_run_duration_by_status(policy_id, start_date, end_date, versions)


@router.post("/{policy_id}/runs/count/query", response_model=list[Any])
def runs_by_policy(
    policy_id: str,
    start_date: datetime.date | None = None,
    end_date: datetime.date | None = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    service: PolicyAnalyticsService = Depends(get_policy_analytics_service),
):
    """Get run counts and error rates for a policy."""
    return service.get_run_counts(policy_id, start_date, end_date, versions)


@router.post("/{policy_id}/runs/outcomes/query", response_model=list[Any])
def runs_outcomes_by_policy(
    policy_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    versions: Annotated[list[str] | None, Body(embed=True)] = None,
    service: PolicyAnalyticsService = Depends(get_policy_analytics_service),
):
    """Get run outcome distribution for a policy."""
    return service.get_run_outcomes(policy_id, start_date, end_date, versions)
