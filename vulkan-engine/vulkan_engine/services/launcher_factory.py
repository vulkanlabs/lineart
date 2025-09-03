"""Factory for creating workflow engine launchers.

This module provides abstractions and factory methods for creating
run launchers that work with different workflow engines (Dagster, Hatchet).
"""

from abc import ABC, abstractmethod
from uuid import UUID

from sqlalchemy.orm import Session
from vulkan_engine.config import DagsterServiceConfig, VulkanEngineConfig
from vulkan_engine.dagster.client import create_dagster_client_from_config
from vulkan_engine.dagster.launch_run import DagsterRunLauncher
from vulkan_engine.db import Run


class WorkerLauncher(ABC):
    """Abstract base class for workflow engine run launchers."""

    @abstractmethod
    def create_run(
        self,
        input_data: dict,
        policy_version_id: str,
        run_group_id: UUID | None = None,
        run_config_variables: dict[str, str] | None = None,
        project_id: UUID | None = None,
    ) -> Run:
        """Create and launch a run in the workflow engine.

        Args:
            input_data: Input data for the run
            policy_version_id: ID of the policy version to execute
            run_group_id: Optional run group ID for batching runs
            run_config_variables: Optional configuration variables for the run
            project_id: Optional project ID for access control

        Returns:
            Created run instance
        """
        pass


class LauncherFactory:
    """Factory for creating workflow engine launchers."""

    @staticmethod
    def create_launcher(config: VulkanEngineConfig, db: Session) -> WorkerLauncher:
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
            return LauncherFactory._create_dagster_launcher(config, db)
        elif worker_type == "hatchet":
            return LauncherFactory._create_hatchet_launcher(config, db)
        else:
            raise ValueError(f"Unsupported worker type: {worker_type}")

    @staticmethod
    def _create_dagster_launcher(
        config: VulkanEngineConfig, db: Session
    ) -> WorkerLauncher:
        """Create Dagster launcher with proper configuration."""
        dagster_config = DagsterServiceConfig(
            host=config.worker_service.host,
            port=config.worker_service.port,
            server_port=config.worker_service.server_port or config.worker_service.port,
        )
        dagster_client = create_dagster_client_from_config(dagster_config)
        server_url = dagster_config.server_url

        return DagsterRunLauncher(
            db=db, dagster_client=dagster_client, server_url=server_url
        )

    @staticmethod
    def _create_hatchet_launcher(
        config: VulkanEngineConfig, db: Session
    ) -> WorkerLauncher:
        """Create Hatchet launcher with proper configuration."""
        # For now, raise NotImplementedError since Hatchet launcher doesn't exist yet
        raise NotImplementedError("Hatchet launcher is not yet implemented")

        # Future implementation would look like:
        # try:
        #     from vulkan_engine.hatchet.launch_run import HatchetRunLauncher
        # except ImportError as e:
        #     raise ImportError(f"Hatchet dependencies not available: {e}")
        #
        # return HatchetRunLauncher(db=db, config=config.worker_service)
