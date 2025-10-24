"""
Dependency injection providers for vulkan-server.

Provides centralized dependency injection for FastAPI routers following clean architecture principles.
All service dependencies are configured here to ensure consistency and maintainability.

Organization:
- Configuration Dependencies: Core app configuration and settings
- Infrastructure Dependencies: Database, logging, external clients
- Service Dependencies: Business logic services for routers
"""

import os
from functools import lru_cache
from typing import Annotated, Iterator

import redis
from fastapi import Depends
from sqlalchemy.orm import Session
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.backends.factory.backend import ExecutionBackendFactory
from vulkan_engine.backends.factory.data_client import BaseDataClient, DataClientFactory
from vulkan_engine.backends.factory.service_client import (
    BackendServiceClient,
    ServiceClientFactory,
)
from vulkan_engine.config import VulkanEngineConfig

# Removed legacy Dagster imports - now using worker abstractions only
from vulkan_engine.db import get_db_session
from vulkan_engine.logger import VulkanLogger, create_logger
from vulkan_engine.services import (
    AllocationService,
    ComponentService,
    DataSourceAnalyticsService,
    DataSourceService,
    DataSourceTestService,
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


def get_redis_client() -> redis.Redis | None:
    """
    Get Redis client for OAuth token caching.

    Returns:
        Redis client instance or None if Redis is not configured

    Envs:
        REDIS_HOST: Redis server host (default localhost)
        REDIS_PORT: Redis server port (default 6379)
        REDIS_DB: Redis database number (default 0)
        REDIS_PASSWORD: Redis password (optional)
    """
    redis_host = os.getenv("REDIS_HOST")

    if not redis_host:
        return None

    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))
    redis_password = os.getenv("REDIS_PASSWORD")

    try:
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            db=redis_db,
            password=redis_password if redis_password else None,
            decode_responses=False,
        )
        client.ping()
        return client
    except (redis.ConnectionError, redis.TimeoutError):
        return None


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


def get_execution_backend(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
) -> ExecutionBackend:
    """
    Get execution backend for running workflows.

    Args:
        launcher: Worker launcher (Dagster, Hatchet, etc.)
        config: Vulkan engine configuration

    Returns:
        ExecutionBackend instance (currently DagsterBackend)
    """
    return ExecutionBackendFactory.create_backend(config)


def get_worker_data_client(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
    db_session: Annotated[Session, Depends(get_database_session)],
) -> BaseDataClient | None:
    """
    Get worker data client using factory pattern.

    Args:
        config: Vulkan engine configuration
        db_session: App database session

    Returns:
        WorkerDataClient instance or None if database is disabled
    """
    factory = DataClientFactory(db_session)
    return factory.create_data_client(config)


def get_worker_service_client(
    config: Annotated[VulkanEngineConfig, Depends(get_vulkan_server_config)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> BackendServiceClient:
    """
    Get worker service client using factory pattern.

    Args:
        config: Vulkan engine configuration

    Returns:
        WorkerServiceClient instance (Dagster, Hatchet, etc.)
    """
    return ServiceClientFactory.create_service_client(config, base_logger=logger)


# Business Service Dependencies
def get_run_query_service(
    db: Annotated[Session, Depends(get_database_session)],
    worker_data_client: Annotated[
        BaseDataClient | None, Depends(get_worker_data_client)
    ],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> RunQueryService:
    """
    Get RunQueryService for read operations.

    Args:
        db: Database session
        worker_data_client: Worker data client (may be None if database disabled)
        logger: Configured logger

    Returns:
        Configured RunQueryService instance
    """
    if worker_data_client is None:
        raise ValueError("Worker data client is required")
    return RunQueryService(
        db=db,
        data_client=worker_data_client,
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
    worker_service_client: Annotated[
        BackendServiceClient, Depends(get_worker_service_client)
    ],
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> WorkflowService:
    """Get WorkflowService instance with dependencies."""
    return WorkflowService(
        db=db, backend_service_client=worker_service_client, logger=logger
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
    redis_cache: Annotated[redis.Redis | None, Depends(get_redis_client)],
) -> DataSourceService:
    """
    Get DataSourceService for data source management.

    Args:
        db: Database session
        logger: Configured logger
        redis_cache: Redis client for OAuth token caching (optional)

    Returns:
        Configured DataSourceService instance
    """
    return DataSourceService(db=db, logger=logger, redis_cache=redis_cache)


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


def get_data_source_test_service(
    db: Annotated[Session, Depends(get_database_session)],
    logger: Annotated[VulkanLogger, Depends(get_configured_logger)],
) -> DataSourceTestService:
    """
    Get DataSourceTestService for testing data sources.

    Args:
        db: Database session
        logger: Configured logger

    Returns:
        Configured DataSourceTestService instance
    """
    return DataSourceTestService(db=db, logger=logger)
