"""Factory for creating worker service clients.

This module provides abstractions and factory methods for creating
service clients that work with different workflow engines' HTTP services.
"""

import os
from logging import Logger

from vulkan_engine.backends.dagster.client import (
    DagsterServiceConfig,
    create_dagster_client_from_config,
)
from vulkan_engine.backends.dagster.service_client import DagsterServiceClient
from vulkan_engine.backends.hatchet.service_client import (
    HatchetRequestConfig,
    HatchetServiceClient,
)
from vulkan_engine.backends.service_client import BackendServiceClient
from vulkan_engine.config import (
    DagsterConfig,
    HatchetConfig,
    VulkanEngineConfig,
    WorkerServiceConfig,
)


class ServiceClientFactory:
    """Factory for creating workflow engine service clients."""

    @staticmethod
    def create_service_client(
        config: VulkanEngineConfig,
        base_logger: Logger,
    ) -> BackendServiceClient:
        """Create a service client based on the configuration.

        Args:
            config: VulkanEngine configuration
            base_logger: Logger instance used to create the service logger

        Returns:
            Appropriate service client implementation

        Raises:
            ValueError: If the worker type is not supported
        """
        worker_type = config.worker_service.worker_type

        if worker_type == "dagster":
            return ServiceClientFactory._create_dagster_service_client(
                config, base_logger
            )
        elif worker_type == "hatchet":
            return ServiceClientFactory._create_hatchet_service_client(
                config, base_logger
            )
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_service_client(
        config: VulkanEngineConfig,
        base_logger: Logger,
    ) -> DagsterServiceClient:
        """Create Dagster service client with proper configuration."""

        # Check if using new WorkerServiceConfig structure
        if hasattr(config.worker_service, "service_config") and isinstance(
            config.worker_service.service_config, DagsterConfig
        ):
            # For now, DagsterConfig has no fields, but structure is ready for future extensions
            server_url = config.worker_service.server_url
            # Parse host and port from server_url for backward compatibility
            from urllib.parse import urlparse

            parsed = urlparse(server_url)

            dagster_config = DagsterServiceConfig(
                host=parsed.hostname or "localhost",
                port=parsed.port or 3000,
                server_port=parsed.port or 3000,
            )
        else:
            # Fallback for old config structure
            dagster_config = DagsterServiceConfig(
                host=config.worker_service.host,
                port=config.worker_service.port,
                server_port=config.worker_service.server_port
                or config.worker_service.port,
            )

        dagster_client = create_dagster_client_from_config(dagster_config)
        server_url = dagster_config.server_url

        return DagsterServiceClient(
            server_url=server_url,
            dagster_client=dagster_client,
            base_logger=base_logger,
        )

    @staticmethod
    def _create_hatchet_service_client(
        config: VulkanEngineConfig,
        base_logger: Logger,
    ) -> HatchetServiceClient:
        """Create Hatchet service client with proper configuration."""

        server_url = config.worker_service.server_url

        # Access the hatchet-specific config if using WorkerServiceConfig
        hatchet_config = config.worker_service.service_config
        # Pass token through request headers
        request_config = HatchetRequestConfig(
            headers={"Authorization": f"Bearer {hatchet_config.hatchet_token}"}
        )
        return HatchetServiceClient(
            server_url=server_url,
            request_config=request_config,
            logger=base_logger,
        )


SUPPORTED_BACKENDS: set[str] = {"dagster", "hatchet"}


def create_worker_service_config() -> WorkerServiceConfig:
    worker_type = os.getenv("WORKER_TYPE")
    if worker_type not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"Invalid WORKER_TYPE: {worker_type}. Must be one of {SUPPORTED_BACKENDS}"
        )

    worker_url = os.getenv("WORKER_URL")
    if worker_url is None:
        raise ValueError("Missing required environment variable: WORKER_URL")

    if worker_type == "hatchet":
        hatchet_token = os.getenv("HATCHET_TOKEN")
        if hatchet_token is None:
            raise ValueError("Missing required environment variable: HATCHET_TOKEN")
        service_config = HatchetConfig(hatchet_token=hatchet_token)
    elif worker_type == "dagster":
        service_config = DagsterConfig()

    return WorkerServiceConfig(
        worker_type=worker_type,
        server_url=worker_url,
        service_config=service_config,
    )
