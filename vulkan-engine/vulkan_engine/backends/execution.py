"""Base interface for execution backends."""

from abc import ABC, abstractmethod


class ExecutionBackend(ABC):
    """Abstract base class for workflow execution backends."""

    @abstractmethod
    def trigger_job(
        self,
        run_id: str,
        workflow_id: str,
        input_data: dict,
        # TODO: Hatchet requires the input schema for validation.
        # It validates the input when starting the run, but the status
        # might not be too nice.
        # This might be an opportunity for us to handle validation more
        # explicitly in the app, before triggering runs.
        input_schema: dict,
        config_variables: dict[str, str],
        project_id: str | None = None,
    ) -> str:
        """
        Trigger a job execution in the backend system.

        Args:
            run_id: UUID of the run
            workflow_id: ID of the workflow to execute
            input_data: Input data for the workflow
            input_schema: Input schema for the workflow
            config_variables: Configuration variables for the workflow
            project_id: Optional project UUID

        Returns:
            Backend-specific execution ID (e.g., Dagster run ID)

        Raises:
            Exception: If job triggering fails
        """
        pass
