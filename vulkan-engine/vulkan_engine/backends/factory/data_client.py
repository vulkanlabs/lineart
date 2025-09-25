"""Factory for creating workflow engine data clients.

This module provides abstractions and factory methods for creating
data clients that work with different workflow engines' databases.
"""

from vulkan_engine.backends.dagster.data_client import (
    DagsterDatabaseConfig,
    DagsterDataClient,
)
from vulkan_engine.backends.data_client import BaseDataClient
from vulkan_engine.backends.hatchet.data_client import HatchetDataClient
from vulkan_engine.config import VulkanEngineConfig


class DataClientFactory:
    """Factory for creating workflow engine data clients."""

    @staticmethod
    def create_data_client(config: VulkanEngineConfig) -> BaseDataClient | None:
        """Create a data client based on the configuration.

        Args:
            config: VulkanEngine configuration

        Returns:
            Appropriate data client implementation, or None if database is disabled

        Raises:
            ValueError: If the worker type is not supported
        """
        if not config.worker_database.enabled:
            return None

        worker_type = config.worker_service.worker_type

        if worker_type == "dagster":
            return DataClientFactory._create_dagster_data_client(config)
        elif worker_type == "hatchet":
            return DataClientFactory._create_hatchet_data_client(config)
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_data_client(config: VulkanEngineConfig) -> BaseDataClient:
        """Create Dagster data client with proper configuration."""

        # Create equivalent DagsterDatabaseConfig from WorkerDatabaseConfig
        if not config.worker_database.connection_string:
            raise ValueError(
                "Worker database is enabled but missing required connection parameters"
            )

        dagster_db_config = DagsterDatabaseConfig(
            user=config.worker_database.user,
            password=config.worker_database.password,
            host=config.worker_database.host,
            port=config.worker_database.port,
            database=config.worker_database.database,
        )
        return DagsterDataClient(dagster_db_config)

    @staticmethod
    def _create_hatchet_data_client(config: VulkanEngineConfig) -> BaseDataClient:
        """Create Hatchet data client with proper configuration."""
        return HatchetDataClient(
            worker_config=config.worker_service,
        )
