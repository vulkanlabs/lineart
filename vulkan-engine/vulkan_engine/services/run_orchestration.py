"""
Run orchestration service for run management and execution.

Handles all operations related to run creation, status updates,
and shadow run triggering.
"""

from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from vulkan.core.run import RunStatus
from vulkan_engine.dagster.launch_run import DagsterRunLauncher
from vulkan_engine.db import Run, RunGroup, StepMetadata
from vulkan_engine.loaders import RunLoader
from vulkan_engine.schemas import StepMetadataBase
from vulkan_engine.services.base import BaseService
from vulkan_engine.validators import validate_uuid, validate_optional_uuid
from vulkan_engine.exceptions import RunNotFoundException


class RunOrchestrationService(BaseService):
    """Service for orchestrating run execution and management."""

    def __init__(
        self,
        db: Session,
        launcher: DagsterRunLauncher,
        logger=None,
    ):
        """
        Initialize run orchestration service.

        Args:
            db: Database session
            launcher: Dagster run launcher for run execution
            logger: Logger instance
        """
        super().__init__(db, logger)
        self.launcher = launcher
        self.run_loader = RunLoader(db)

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
        # Validate run ID
        validate_uuid(run_id, "run")

        run = self.db.query(Run).filter_by(run_id=run_id).first()
        if not run:
            raise RunNotFoundException(f"Run {run_id} not found")
        return run

    def publish_step_metadata(
        self, run_id: str, metadata: StepMetadataBase, project_id: str = None
    ) -> dict[str, str]:
        """
        Publish metadata for a run step.

        Args:
            run_id: Run UUID
            metadata: Step metadata to publish
            project_id: Optional project UUID to filter by

        Returns:
            Success status dict

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
        """
        # Validate run ID
        validate_uuid(run_id, "run")

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
        project_id: str = None,
    ) -> Run:
        """
        Update run status and optionally trigger shadow runs.

        Args:
            run_id: Run UUID
            status: New status string
            result: Run result
            metadata: Optional run metadata
            project_id: Optional project UUID to filter by

        Returns:
            Updated Run object

        Raises:
            RunNotFoundException: If run doesn't exist or doesn't belong to specified project
            ValueError: If status is invalid
        """
        # Validate run ID
        validate_uuid(run_id, "run")

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

        self.logger.system.info(f"Run group_id {run.run_group_id}")

        # Trigger shadow runs if part of a run group
        # TODO: What to do when the main run fails?
        # TODO: Should we trigger the remaining runs with a subprocess (so we don't
        # halt the API's response)?
        if run.run_group_id:
            self.logger.system.info(
                f"Launching shadow runs from group {run.run_group_id}"
            )
            self._trigger_pending_runs(run.run_group_id)

        return run

    def _trigger_pending_runs(self, run_group_id: UUID) -> None:
        """
        Trigger pending runs in a run group.

        Args:
            run_group_id: Run group UUID
        """
        # Get run group and input data
        run_group = self.db.query(RunGroup).filter_by(run_group_id=run_group_id).first()
        if not run_group:
            self.logger.system.error(f"Run group {run_group_id} not found")
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
            self.logger.system.info(f"Launching run {run.run_id}")
            try:
                self.launcher.launch_run(run=run, input_data=input_data)
            except Exception as e:
                # TODO: Structure log to trace the run that failed and the way it was triggered
                self.logger.system.error(f"Failed to launch run {run.run_id}: {e}")
                continue
