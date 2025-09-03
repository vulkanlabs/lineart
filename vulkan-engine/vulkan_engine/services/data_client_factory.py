"""Factory for creating workflow engine data clients.

This module provides abstractions and factory methods for creating
data clients that work with different workflow engines' databases.
"""

from abc import ABC, abstractmethod
from typing import Any

from vulkan_engine.config import VulkanEngineConfig
from vulkan_engine.schemas import LogEntry


class WorkerDataClient(ABC):
    """Abstract base class for workflow engine data clients."""

    @abstractmethod
    def get_run_data(self, run_id: str) -> list[tuple[str, str, str]]:
        """Get run data for a specific run.

        Args:
            run_id: The run identifier

        Returns:
            List of tuples containing (step_name, object_name, value)
        """
        pass

    @abstractmethod
    def get_run_logs(self, run_id: str) -> list[LogEntry]:
        """Get logs for a specific run.

        Args:
            run_id: The run identifier

        Returns:
            List of log entries
        """
        pass


class DataClientFactory:
    """Factory for creating workflow engine data clients."""

    @staticmethod
    def create_data_client(config: VulkanEngineConfig) -> WorkerDataClient | None:
        """Create a data client based on the configuration.

        Args:
            config: VulkanEngine configuration

        Returns:
            Appropriate data client implementation, or None if database is disabled

        Raises:
            ValueError: If the worker type is not supported
            ImportError: If required dependencies are not available
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
    def _create_dagster_data_client(config: VulkanEngineConfig) -> WorkerDataClient:
        """Create Dagster data client with proper configuration."""
        try:
            from vulkan_engine.dagster.client import (
                DagsterDataClient,
                create_dagster_data_client,
            )
        except ImportError as e:
            raise ImportError(f"Dagster dependencies not available: {e}")

        # Create equivalent DagsterDatabaseConfig from WorkerDatabaseConfig
        from vulkan_engine.config import DagsterDatabaseConfig

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
        return create_dagster_data_client(dagster_db_config)

    @staticmethod
    def _create_hatchet_data_client(config: VulkanEngineConfig) -> WorkerDataClient:
        """Create Hatchet data client with proper configuration."""
        # For now, raise NotImplementedError since Hatchet data client doesn't exist yet
        raise NotImplementedError("Hatchet data client is not yet implemented")

        # Future implementation would look like:
        # try:
        #     from vulkan_engine.hatchet.client import HatchetDataClient
        # except ImportError as e:
        #     raise ImportError(f"Hatchet dependencies not available: {e}")
        #
        # return HatchetDataClient(config=config.worker_database)
