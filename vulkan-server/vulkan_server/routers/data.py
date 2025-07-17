"""
Data source and data broker management router.

Handles HTTP endpoints for data source operations. All business logic
is delegated to DataSourceService.
"""

import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from vulkan_engine import schemas
from vulkan_engine.exceptions import (
    DataBrokerException,
    DataBrokerRequestException,
    DataSourceAlreadyExistsException,
    DataSourceNotFoundException,
    InvalidDataSourceException,
)
from vulkan_engine.services import DataSourceAnalyticsService, DataSourceService

from vulkan.schemas import DataSourceSpec
from vulkan_server.dependencies import (
    get_data_source_analytics_service,
    get_data_source_service,
)

sources = APIRouter(
    prefix="/data-sources",
    tags=["data-sources"],
    responses={404: {"description": "Not found"}},
)


@sources.get("/", response_model=list[schemas.DataSource])
def list_data_sources(
    include_archived: bool = False,
    service: DataSourceService = Depends(get_data_source_service),
):
    """List all data sources."""
    data_sources = service.list_data_sources(include_archived=include_archived)
    return [schemas.DataSource.from_orm(ds) for ds in data_sources]


@sources.post("/")
def create_data_source(
    spec: DataSourceSpec,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Create a new data source."""
    try:
        return service.create_data_source(spec)
    except DataSourceAlreadyExistsException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except InvalidDataSourceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@sources.get("/{data_source_id}", response_model=schemas.DataSource)
def get_data_source(
    data_source_id: str,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Get a data source by ID."""
    try:
        data_source = service.get_data_source(data_source_id)
        return schemas.DataSource.from_orm(data_source)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@sources.delete("/{data_source_id}")
def delete_data_source(
    data_source_id: str,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Delete (archive) a data source."""
    try:
        return service.delete_data_source(data_source_id)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDataSourceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@sources.put("/{data_source_id}/variables")
def set_data_source_env_variables(
    data_source_id: str,
    desired_variables: Annotated[list[schemas.DataSourceEnvVarBase], Body()],
    service: DataSourceService = Depends(get_data_source_service),
):
    """Set environment variables for a data source."""
    try:
        return service.set_environment_variables(data_source_id, desired_variables)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InvalidDataSourceException as e:
        raise HTTPException(status_code=400, detail=str(e))


@sources.get(
    "/{data_source_id}/variables", response_model=list[schemas.DataSourceEnvVar]
)
def get_data_source_env_variables(
    data_source_id: str,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Get environment variables for a data source."""
    try:
        return service.get_environment_variables(data_source_id)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@sources.get(
    "/{data_source_id}/objects", response_model=list[schemas.DataObjectMetadata]
)
def list_data_objects(
    data_source_id: str,
    service: DataSourceService = Depends(get_data_source_service),
):
    """List data objects for a data source."""
    try:
        return service.list_data_objects(data_source_id)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@sources.get(
    "/{data_source_id}/objects/{data_object_id}", response_model=schemas.DataObject
)
def get_data_object(
    data_source_id: str,
    data_object_id: str,
    service: DataSourceService = Depends(get_data_source_service),
):
    """Get a specific data object."""
    try:
        return service.get_data_object(data_source_id, data_object_id)
    except DataSourceNotFoundException as e:
        raise HTTPException(status_code=404, detail=str(e))


@sources.get("/{data_source_id}/usage", response_model=dict[str, Any])
def get_data_source_usage(
    data_source_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    service: DataSourceAnalyticsService = Depends(get_data_source_analytics_service),
):
    """Get usage statistics for a data source."""
    return service.get_usage_statistics(data_source_id, start_date, end_date)


@sources.get("/{data_source_id}/metrics", response_model=dict[str, Any])
def get_data_source_metrics(
    data_source_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    service: DataSourceAnalyticsService = Depends(get_data_source_analytics_service),
):
    """Get performance metrics for a data source."""
    return service.get_performance_metrics(data_source_id, start_date, end_date)


@sources.get("/{data_source_id}/cache-stats", response_model=dict[str, Any])
def get_cache_statistics(
    data_source_id: str,
    start_date: Annotated[datetime.date | None, Query()] = None,
    end_date: Annotated[datetime.date | None, Query()] = None,
    service: DataSourceAnalyticsService = Depends(get_data_source_analytics_service),
):
    """Get cache statistics for a data source."""
    return service.get_cache_statistics(data_source_id, start_date, end_date)


# Data Broker Router
broker = APIRouter(
    prefix="/data-broker",
    tags=["data-broker"],
    responses={404: {"description": "Not found"}},
)


@broker.post("/", response_model=schemas.DataBrokerResponse)
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
