"""Factory for creating worker service clients.

This module provides abstractions and factory methods for creating
service clients that work with different workflow engines' HTTP services.
"""

from vulkan_engine.config import DagsterServiceConfig, VulkanEngineConfig
from vulkan_engine.dagster.client import create_dagster_client_from_config
from vulkan_engine.dagster.service_client import VulkanDagsterServiceClient
from vulkan_engine.hatchet.service_client import HatchetServiceClient
from vulkan_engine.services.base import WorkerServiceClient


class WorkerServiceClientFactory:
    """Factory for creating workflow engine service clients."""

    @staticmethod
    def create_service_client(config: VulkanEngineConfig) -> WorkerServiceClient:
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
            return WorkerServiceClientFactory._create_dagster_service_client(config)
        elif worker_type == "hatchet":
            return WorkerServiceClientFactory._create_hatchet_service_client(config)
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_service_client(
        config: VulkanEngineConfig,
    ) -> VulkanDagsterServiceClient:
        """Create Dagster service client with proper configuration."""

        dagster_config = DagsterServiceConfig(
            host=config.worker_service.host,
            port=config.worker_service.port,
            server_port=config.worker_service.server_port or config.worker_service.port,
        )
        dagster_client = create_dagster_client_from_config(dagster_config)
        server_url = dagster_config.server_url

        return VulkanDagsterServiceClient(
            server_url=server_url,
            dagster_client=dagster_client,
        )

    @staticmethod
    def _create_hatchet_service_client(
        config: VulkanEngineConfig,
    ) -> HatchetServiceClient:
        """Create Hatchet service client with proper configuration."""

        server_url = config.worker_service.server_url
        return HatchetServiceClient(server_url=server_url)
