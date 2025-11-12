"""Factory for creating worker service clients.

This module provides abstractions and factory methods for creating
service clients that work with different workflow engines' HTTP services.
"""

import os

from vulkan_engine.backends.dagster.client import (
    create_dagster_client_from_url,
)
from vulkan_engine.backends.dagster.service_client import DagsterServiceClient
from vulkan_engine.backends.hatchet.service_client import (
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
    ) -> BackendServiceClient:
        """Create a service client based on the configuration.

        Args:
            config: VulkanEngine configuration

        Returns:
            Appropriate service client implementation

        Raises:
            ValueError: If the worker type is not supported
        """
        worker_type = config.worker_service.worker_type

        if worker_type == "dagster":
            return ServiceClientFactory._create_dagster_service_client(config)
        elif worker_type == "hatchet":
            return ServiceClientFactory._create_hatchet_service_client(config)
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_service_client(
        config: VulkanEngineConfig,
    ) -> DagsterServiceClient:
        """Create Dagster service client with proper configuration."""

        if not isinstance(config.worker_service.service_config, DagsterConfig):
            raise ValueError(
                f"Invalid worker service configuration: {config.worker_service.service_config}"
            )

        try:
            url = config.worker_service.service_config.worker_url
            dagster_client = create_dagster_client_from_url(url)
        except Exception as e:
            raise ValueError("Failed to create Dagster client") from e

        return DagsterServiceClient(
            server_url=config.worker_service.server_url,
            dagster_client=dagster_client,
        )

    @staticmethod
    def _create_hatchet_service_client(
        config: VulkanEngineConfig,
    ) -> HatchetServiceClient:
        """Create Hatchet service client with proper configuration."""

        server_url = config.worker_service.server_url
        return HatchetServiceClient(
            server_url=server_url,
        )


SUPPORTED_BACKENDS: set[str] = {"dagster", "hatchet"}


def create_worker_service_config() -> WorkerServiceConfig:
    worker_type = os.getenv("WORKER_TYPE")
    if worker_type not in SUPPORTED_BACKENDS:
        raise ValueError(
            f"Invalid WORKER_TYPE: {worker_type}. Must be one of {SUPPORTED_BACKENDS}"
        )

    server_url = os.getenv("BACKEND_SERVER_URL")
    if server_url is None:
        msg = "Missing required environment variable: BACKEND_SERVER_URL"
        raise ValueError(msg)

    if worker_type == "hatchet":
        hatchet_token = os.getenv("HATCHET_CLIENT_TOKEN")
        if hatchet_token is None:
            msg = "Missing required environment variable: HATCHET_CLIENT_TOKEN"
            raise ValueError(msg)
        service_config = HatchetConfig(hatchet_token=hatchet_token)
    elif worker_type == "dagster":
        worker_url = os.getenv("DAGSTER_WORKER_URL")
        if worker_url is None:
            msg = "Missing required environment variable: DAGSTER_WORKER_URL"
            raise ValueError(msg)
        service_config = DagsterConfig(worker_url=worker_url)
    else:
        raise ValueError(f"Invalid WORKER_TYPE: {worker_type}")

    return WorkerServiceConfig(
        worker_type=worker_type,
        server_url=server_url,
        service_config=service_config,
    )
