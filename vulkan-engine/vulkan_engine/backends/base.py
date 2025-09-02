"""Base interface for execution backends."""

from abc import ABC, abstractmethod
from uuid import UUID


class ExecutionBackend(ABC):
    """Abstract base class for workflow execution backends."""

    @abstractmethod
    def trigger_job(
        self,
        run_id: UUID,
        workflow_id: str,
        input_data: dict,
        config_variables: dict[str, str],
        project_id: UUID | None = None,
    ) -> str:
        """
        Trigger a job execution in the backend system.

        Args:
            run_id: UUID of the run
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            config_variables: Configuration variables for the workflow
            project_id: Optional project UUID

        Returns:
            Backend-specific execution ID (e.g., Dagster run ID)

        Raises:
            Exception: If job triggering fails
        """
        pass
