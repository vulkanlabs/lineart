"""
Run query service for read-only operations.

Handles all read operations related to runs including data retrieval,
logs, and metadata queries.
"""

from sqlalchemy.orm import Session

from vulkan_engine.backends.data_client import BaseDataClient
from vulkan_engine.db import Run
from vulkan_engine.loaders import RunLoader
from vulkan_engine.schemas import RunData, RunLogs
from vulkan_engine.services.base import BaseService


class RunQueryService(BaseService):
    """Service for querying run data and metadata."""

    def __init__(
        self,
        db: Session,
        data_client: BaseDataClient,
    ):
        """
        Initialize run query service.

        Args:
            db: Database session
            data_client: Backend data client for retrieving run data
        """
        super().__init__(db)
        self.data_client = data_client
        self.run_loader = RunLoader(db)

    def get_run(self, run_id: str, project_id: str | None = None) -> Run:
        """
        Get a run by ID, optionally filtered by project.

        Args:
            run_id: Run UUID
            project_id: Optional project UUID to filter by

        Returns:
            Run object

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
        """
        return self.run_loader.get_run(run_id, project_id=project_id)

    def get_run_data(self, run_id: str, project_id: str | None = None) -> RunData:
        """
        Get run data including step outputs and metadata.

        Args:
            run_id: Run UUID
            project_id: Optional project UUID to filter by

        Returns:
            RunData object with steps and outputs

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
            Exception: If data unpickling fails
        """
        run = self.run_loader.get_run(run_id, project_id=project_id)

        # Initialize run data structure
        run_data = RunData.model_validate(run)

        # Get data from execution backend
        steps = self.data_client.get_run_data(run.backend_run_id)
        if not steps:
            return run_data
        run_data.steps = steps

        return run_data

    def get_run_logs(self, run_id: str, project_id: str | None = None) -> RunLogs:
        """
        Get logs for a run.

        Args:
            run_id: Run UUID
            project_id: Optional project UUID to filter by

        Returns:
            RunLogs object

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
        """
        run = self.run_loader.get_run(run_id, project_id=project_id)
        logs = self.data_client.get_run_logs(run.backend_run_id)

        return RunLogs(
            run_id=run_id,
            status=run.status,
            last_updated_at=run.last_updated_at,
            logs=logs,
        )
