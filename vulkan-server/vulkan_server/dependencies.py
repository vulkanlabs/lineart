"""
Dependency injection providers for vulkan-server.

Provides centralized dependency injection for FastAPI routers following clean architecture principles.
All service dependencies are configured here to ensure consistency and maintainability.

Organization:
- Configuration Dependencies: Core app configuration and settings
- Infrastructure Dependencies: Database, logging, external clients
- Service Dependencies: Business logic services for routers
"""

from functools import lru_cache
from typing import Annotated, Iterator

from fastapi import Depends
from sqlalchemy.orm import Session
from vulkan_engine.backends.base import ExecutionBackend
from vulkan_engine.backends.dagster import DagsterBackend
from vulkan_engine.config import VulkanEngineConfig
from vulkan_engine.dagster.client import (
    DagsterDataClient,
    create_dagster_client_from_config,
)
from vulkan_engine.dagster.service_client import VulkanDagsterServiceClient
from vulkan_engine.db import get_db_session
from vulkan_engine.logger import VulkanLogger, create_logger
from vulkan_engine.services import (
    AllocationService,
    ComponentService,
    DataSourceAnalyticsService,
    DataSourceService,
    PolicyAnalyticsService,
    PolicyService,
    PolicyVersionService,
)
from vulkan_engine.services.credential.credential import CredentialService
from vulkan_engine.services.run_orchestration import RunOrchestrationService
from vulkan_engine.services.run_query import RunQueryService
from vulkan_engine.services.workflow import WorkflowService

from vulkan_server.config import load_vulkan_engine_config


@lru_cache
def get_vulkan_server_config() -> VulkanEngineConfig:
    """
    Get the complete vulkan-server configuration.

    Returns:
        VulkanEngineConfig instance loaded from environment variables
    """
    return load_vulkan_engine_config()


# Infrastructure Dependencies


def get_database_session(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
) -> Iterator[Session]:
    """
    Get database session using configuration.

    Args:
        config: Vulkan engine configuration

    Yields:
        Database session
    """
    yield from get_db_session(config.database)


def get_configured_logger(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
    db: Annotated[Session, Depends(get_database_session)],
) -> VulkanLogger:
    """
    Get configured logger instance.

    Args:
        config: Vulkan engine configuration
        db: Database session

    Returns:
        Configured VulkanLogger instance
    """
    return create_logger(db, config.logging)


def get_service_dependencies(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> tuple[Session, VulkanLogger]:
    """
    Get common dependencies for services.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Tuple of (database session, logger)
    """
    return db, logger


def get_dagster_client(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
):
    """
    Get Dagster client using configuration.

    Args:
        config: Vulkan engine configuration

    Returns:
        Dagster GraphQL client
    """
    return create_dagster_client_from_config(config.dagster_service)


def get_execution_backend(
    dagster_client: Annotated[object, Depends(get_dagster_client)],
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
) -> ExecutionBackend:
    """
    Get execution backend for running workflows.

    Args:
        dagster_client: Dagster GraphQL client
        config: Vulkan engine configuration

    Returns:
        ExecutionBackend instance (currently DagsterBackend)
    """
    return DagsterBackend(
        dagster_client=dagster_client,
        server_url=config.app.server_url,
    )


def get_dagster_service_client(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
    dagster_client: Annotated[object, Depends(get_dagster_client)],
) -> VulkanDagsterServiceClient:
    """
    Get Dagster service client.

    Args:
        config: Vulkan engine configuration
        dagster_client: Dagster GraphQL client

    Returns:
        VulkanDagsterServiceClient instance
    """
    return VulkanDagsterServiceClient(
        server_url=config.vulkan_dagster_server_url,
        dagster_client=dagster_client,
    )


def get_dagster_data_client(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
) -> DagsterDataClient:
    """
    Get Dagster data client.

    Args:
        config: Vulkan engine configuration

    Returns:
        DagsterDataClient instance
    """
    return DagsterDataClient(config.dagster_database)


# Business Service Dependencies


def get_run_query_service(
    db: Annotated[Session, Depends(get_database_session)],
    dagster_data_client: Annotated[DagsterDataClient, Depends(get_dagster_data_client)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> RunQueryService:
    """
    Get RunQueryService for read operations.

    Args:
        db: Database session
        dagster_data_client: Dagster data client
        logger: Configured logger

    Returns:
        Configured RunQueryService instance
    """
    return RunQueryService(
        db=db,
        dagster_client=dagster_data_client,
        logger=logger,
    )


def get_run_orchestration_service(
    db: Annotated[Session, Depends(get_database_session)],
    backend: Annotated[ExecutionBackend, Depends(get_execution_backend)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> RunOrchestrationService:
    """
    Get RunOrchestrationService for run management.

    Args:
        db: Database session
        backend: Execution backend for running workflows
        logger: Configured logger

    Returns:
        Configured RunOrchestrationService instance
    """
    return RunOrchestrationService(
        db=db,
        backend=backend,
        logger=logger,
    )


def get_policy_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> PolicyService:
    """
    Get PolicyService for policy management.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured PolicyService instance
    """
    return PolicyService(db=db, logger=logger)


def get_workflow_service(
    dagster_service_client: Annotated[
        VulkanDagsterServiceClient, Depends(get_dagster_service_client)
    ],
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> WorkflowService:
    """Get WorkflowService instance with dependencies."""
    return WorkflowService(
        db=db, dagster_service_client=dagster_service_client, logger=logger
    )


def get_policy_version_service(
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
    orchestrator: Annotated[
        RunOrchestrationService, Depends(get_run_orchestration_service)
    ],
    deps=Depends(get_service_dependencies),
) -> PolicyVersionService:
    """Get PolicyVersionService instance with dependencies."""
    db, logger = deps
    return PolicyVersionService(
        db=db,
        workflow_service=workflow_service,
        orchestrator=orchestrator,
        logger=logger,
    )


def get_allocation_service(
    db: Annotated[Session, Depends(get_database_session)],
    orchestrator: Annotated[
        RunOrchestrationService, Depends(get_run_orchestration_service)
    ],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> AllocationService:
    """
    Get AllocationService for run allocation.

    Args:
        db: Database session
        orchestrator: Run orchestration service
        logger: Configured logger

    Returns:
        Configured AllocationService instance
    """
    return AllocationService(db=db, orchestrator=orchestrator, logger=logger)


def get_data_source_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> DataSourceService:
    """
    Get DataSourceService for data source management.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured DataSourceService instance
    """
    return DataSourceService(db=db, logger=logger)


def get_component_service(
    db: Annotated[Session, Depends(get_database_session)],
    workflow_service: Annotated[WorkflowService, Depends(get_workflow_service)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> ComponentService:
    """
    Get ComponentService for component management.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured ComponentService instance
    """
    return ComponentService(db=db, workflow_service=workflow_service, logger=logger)


def get_data_source_analytics_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> DataSourceAnalyticsService:
    """
    Get DataSourceAnalyticsService for data source analytics.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured DataSourceAnalyticsService instance
    """
    return DataSourceAnalyticsService(db=db, logger=logger)


def get_policy_analytics_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> PolicyAnalyticsService:
    """
    Get PolicyAnalyticsService for policy analytics.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured PolicyAnalyticsService instance
    """
    return PolicyAnalyticsService(db=db, logger=logger)


def get_credential_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> CredentialService:
    """
    Get CredentialService for OAuth credential management.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured CredentialService instance
    """
    return CredentialService(db=db, logger=logger)
