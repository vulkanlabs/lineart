"""Factory for creating workflow engine launchers.

This module provides abstractions and factory methods for creating
run launchers that work with different workflow engines (Dagster, Hatchet).
"""

from vulkan_engine.backends.dagster.backend import DagsterBackend
from vulkan_engine.backends.dagster.client import create_dagster_client_from_config
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.backends.hatchet.backend import HatchetBackend
from vulkan_engine.config import DagsterServiceConfig, VulkanEngineConfig


class ExecutionBackendFactory:
    """Factory for creating workflow engine launchers."""

    @staticmethod
    def create_backend(config: VulkanEngineConfig) -> ExecutionBackend:
        """Create a launcher based on the configuration.

        Args:
            config: VulkanEngine configuration
            db: Database session

        Returns:
            Appropriate launcher implementation

        Raises:
            ValueError: If the worker type is not supported
            ImportError: If required dependencies are not available
        """
        worker_type = config.worker_service.worker_type

        if worker_type == "dagster":
            return ExecutionBackendFactory._create_dagster_backend(config)
        elif worker_type == "hatchet":
            return ExecutionBackendFactory._create_hatchet_backend(config)
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_backend(
        config: VulkanEngineConfig,
    ) -> ExecutionBackend:
        """Create Dagster launcher with proper configuration."""
        dagster_config = DagsterServiceConfig(
            host=config.worker_service.host,
            port=config.worker_service.port,
            server_port=config.worker_service.server_port or config.worker_service.port,
        )
        dagster_client = create_dagster_client_from_config(dagster_config)

        return DagsterBackend(dagster_client, config.worker_service.server_url)

    @staticmethod
    def _create_hatchet_backend(
        config: VulkanEngineConfig,
    ) -> ExecutionBackend:
        """Create Hatchet launcher with proper configuration."""
        return HatchetBackend(server_url=config.worker_service.server_url)
