from abc import ABC, abstractmethod

from vulkan_engine.schemas import LogEntry, StepDetails

PYTHON_LOG_LEVELS = {
    10: "DEBUG",
    20: "INFO",
    30: "WARNING",
    40: "ERROR",
    50: "CRITICAL",
}


class BaseDataClient(ABC):
    """Abstract base class for workflow engine data clients."""

    @abstractmethod
    def get_run_data(self, run_id: str) -> dict[str, StepDetails]:
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
