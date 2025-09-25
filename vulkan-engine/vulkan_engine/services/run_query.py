"""
Run query service for read-only operations.

Handles all read operations related to runs including data retrieval,
logs, and metadata queries.
"""

import pickle

from sqlalchemy.orm import Session

from vulkan_engine.backends.dagster.data_client import DagsterDataClient
from vulkan_engine.db import Run, StepMetadata
from vulkan_engine.loaders import RunLoader
from vulkan_engine.schemas import RunData, RunLogs
from vulkan_engine.services.base import BaseService


class RunQueryService(BaseService):
    """Service for querying run data and metadata."""

    def __init__(
        self,
        db: Session,
        dagster_client: DagsterDataClient,
        logger=None,
    ):
        """
        Initialize run query service.

        Args:
            db: Database session
            dagster_client: Dagster data client for retrieving run data
            logger: Logger instance
        """
        super().__init__(db, logger)
        self.dagster_client = dagster_client
        self.run_loader = RunLoader(db)

    def get_run(self, run_id: str, project_id: str = None) -> Run:
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

    def get_run_data(self, run_id: str, project_id: str = None) -> RunData:
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

        # Get data from Dagster
        # TODO: START of code we can maybe move to data client
        results = self.dagster_client.get_run_data(run_id)
        if not results:
            return run_data

        # Get step metadata
        steps = self.db.query(StepMetadata).filter_by(run_id=run_id).all()
        if not steps:
            return run_data

        # Process results
        results_by_name = {result[0]: (result[1], result[2]) for result in results}
        metadata = {
            step.step_name: {
                "step_name": step.step_name,
                "node_type": step.node_type,
                "start_time": step.start_time,
                "end_time": step.end_time,
                "error": step.error,
                "extra": step.extra,
            }
            for step in steps
        }

        # Parse step data with metadata
        for step_name, step_metadata in metadata.items():
            value = None

            if step_name in results_by_name:
                object_name, value = results_by_name[step_name]
                if object_name != "result":
                    # Branch node output - object_name represents the path taken
                    value = object_name
                else:
                    # Unpickle the actual result
                    try:
                        value = pickle.loads(value)
                    except pickle.UnpicklingError:
                        raise Exception(
                            f"Failed to unpickle data for {step_name}.{object_name}"
                        )

            run_data.steps[step_name] = {"output": value, "metadata": step_metadata}

        return run_data

    def get_run_logs(self, run_id: str, project_id: str = None) -> RunLogs:
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

        # Get logs from Dagster
        logs = self.dagster_client.get_run_logs(run.dagster_run_id)

        return RunLogs(
            run_id=run_id,
            status=run.status,
            last_updated_at=run.last_updated_at,
            logs=logs,
        )
