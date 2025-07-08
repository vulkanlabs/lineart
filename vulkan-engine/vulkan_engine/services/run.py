"""
Run management service.

Handles all business logic related to runs including data retrieval,
status updates, metadata publishing, and shadow run triggering.
"""

import pickle
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan_engine.dagster.client import DagsterDataClient
from vulkan_engine.dagster.launch_run import DagsterRunLauncher
from vulkan_engine.db import Run, RunGroup, StepMetadata
from vulkan_engine.exceptions import RunNotFoundException
from vulkan_engine.logger import init_logger
from vulkan_engine.schemas import RunData, RunLogs, StepMetadataBase
from vulkan_engine.services.base import BaseService


class RunService(BaseService):
    """Service for managing runs and their operations."""

    def __init__(
        self, db: Session, launcher: DagsterRunLauncher | None = None, logger=None
    ):
        """
        Initialize run service.

        Args:
            db: Database session
            launcher: Optional Dagster run launcher for shadow run triggering
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.launcher = launcher
        self.dagster_client = DagsterDataClient()
        self.run_logger = init_logger("runs")

    def get_run(self, run_id: str) -> Run:
        """
        Get a run by ID.

        Args:
            run_id: Run UUID

        Returns:
            Run object

        Raises:
            RunNotFoundException: If run doesn't exist
        """
        run = self.db.query(Run).filter_by(run_id=run_id).first()
        if not run:
            raise RunNotFoundException(f"Run {run_id} not found")
        return run

    def get_run_data(self, run_id: str) -> RunData:
        """
        Get run data including step outputs and metadata.

        Args:
            run_id: Run UUID

        Returns:
            RunData object with steps and outputs

        Raises:
            RunNotFoundException: If run doesn't exist
            Exception: If data unpickling fails
        """
        run = self.get_run(run_id)

        # Initialize run data structure
        run_data = {
            "run_id": run_id,
            "policy_version_id": run.policy_version_id,
            "status": run.status,
            "last_updated_at": run.last_updated_at,
            "steps": {},
        }

        # Get data from Dagster
        results = self.dagster_client.get_run_data(run_id)
        if not results:
            return RunData(**run_data)

        # Get step metadata
        steps = self.db.query(StepMetadata).filter_by(run_id=run_id).all()
        if not steps:
            return RunData(**run_data)

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

            run_data["steps"][step_name] = {"output": value, "metadata": step_metadata}

        return RunData(**run_data)

    def get_run_logs(self, run_id: str) -> RunLogs:
        """
        Get logs for a run.

        Args:
            run_id: Run UUID

        Returns:
            RunLogs object

        Raises:
            RunNotFoundException: If run doesn't exist
        """
        run = self.get_run(run_id)

        # Get logs from Dagster
        logs = self.dagster_client.get_run_logs(run.dagster_run_id)

        return RunLogs(
            run_id=run_id,
            status=run.status,
            last_updated_at=run.last_updated_at,
            logs=logs,
        )

    def publish_step_metadata(
        self, run_id: str, metadata: StepMetadataBase
    ) -> dict[str, str]:
        """
        Publish metadata for a run step.

        Args:
            run_id: Run UUID
            metadata: Step metadata to publish

        Returns:
            Success status dict

        Raises:
            RunNotFoundException: If run doesn't exist
        """
        # Verify run exists
        self.get_run(run_id)

        # Create metadata record
        args = {"run_id": run_id, **metadata.model_dump()}
        meta = StepMetadata(**args)
        self.db.add(meta)
        self.db.commit()

        return {"status": "success"}

    def update_run_status(
        self,
        run_id: str,
        status: str,
        result: str,
        metadata: dict[str, Any] | None = None,
    ) -> Run:
        """
        Update run status and optionally trigger shadow runs.

        Args:
            run_id: Run UUID
            status: New status string
            result: Run result
            metadata: Optional run metadata

        Returns:
            Updated Run object

        Raises:
            RunNotFoundException: If run doesn't exist
            ValueError: If status is invalid
        """
        run = self.get_run(run_id)

        # Validate status
        try:
            status_enum = RunStatus(status)
        except ValueError:
            raise ValueError(f"Invalid run status: {status}")

        # Update run
        run.status = status_enum
        run.result = result
        run.run_metadata = metadata
        self.db.commit()

        self.run_logger.info(f"Run group_id {run.run_group_id}")

        # Trigger shadow runs if part of a run group
        # TODO: What to do when the main run fails?
        # TODO: Should we trigger the remaining runs with a subprocess (so we don't
        # halt the API's response)?
        if run.run_group_id and self.launcher:
            self.run_logger.info(f"Launching shadow runs from group {run.run_group_id}")
            self._trigger_pending_runs(run.run_group_id)

        return run

    def _trigger_pending_runs(self, run_group_id: UUID) -> None:
        """
        Trigger pending runs in a run group.

        Args:
            run_group_id: Run group UUID
        """
        if not self.launcher:
            self.run_logger.warning("No launcher available to trigger pending runs")
            return

        # Get run group and input data
        run_group = self.db.query(RunGroup).filter_by(run_group_id=run_group_id).first()
        if not run_group:
            self.run_logger.error(f"Run group {run_group_id} not found")
            return

        input_data = run_group.input_data

        # Get pending runs
        pending_runs = (
            self.db.query(Run)
            .filter_by(run_group_id=run_group_id, status=RunStatus.PENDING)
            .all()
        )

        # Launch each pending run
        for run in pending_runs:
            self.run_logger.info(f"Launching run {run.run_id}")
            try:
                self.launcher.launch_run(run=run, input_data=input_data)
            except Exception as e:
                # TODO: Structure log to trace the run that failed and the way it was triggered
                self.run_logger.error(f"Failed to launch run {run.run_id}: {e}")
                continue
