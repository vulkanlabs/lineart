"""
Run orchestration service for run management and execution.

Handles all operations related to run creation, status updates,
and shadow run triggering.
"""

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus
from vulkan.spec.policy import PolicyDefinitionDict

from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.config_variables import resolve_config_variables_from_id
from vulkan_engine.db import Run, RunGroup, StepMetadata, Workflow
from vulkan_engine.exceptions import (
    NotFoundException,
    RunPollingTimeoutException,
    UnhandledException,
    VariablesNotSetException,
)
from vulkan_engine.loaders import RunLoader
from vulkan_engine.loaders.policy_version import PolicyVersionLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import RunResult, StepMetadataBase
from vulkan_engine.services.base import BaseService


@dataclass
class RunConfig:
    workflow_id: str
    variables: dict[str, str]


class RunOrchestrationService(BaseService):
    """Service for orchestrating run execution and management."""

    def __init__(
        self,
        db: Session,
        backend: ExecutionBackend,
    ):
        """
        Initialize run orchestration service.

        Args:
            db: Database session
            backend: Execution backend for running workflows
        """
        super().__init__(db)
        self.backend = backend
        self.run_loader = RunLoader(db)
        self.policy_version_loader = PolicyVersionLoader(db)
        self.logger = get_logger(__name__)

    def create_run(
        self,
        input_data: dict,
        policy_version_id: str,
        run_group_id: UUID | None = None,
        run_config_variables: dict[str, str] | None = None,
        project_id: UUID | None = None,
    ) -> Run:
        """
        Create and launch a run.

        Args:
            input_data: Input data for the run
            policy_version_id: Policy version UUID
            run_group_id: Optional run group UUID
            run_config_variables: Optional configuration variables
            project_id: Optional project UUID

        Returns:
            Created and launched Run object

        Raises:
            NotFoundException: If policy version not found
            VariablesNotSetException: If required variables are missing
            UnhandledException: If run launch fails
        """
        # Validate and prepare configuration
        run_config = self._prepare_run_config(
            policy_version_id, project_id, run_config_variables
        )

        # Create run in database
        run = Run(
            policy_version_id=policy_version_id,
            status=RunStatus.PENDING,
            input_data=input_data,
            run_group_id=run_group_id,
            project_id=project_id,
        )
        self.db.add(run)
        self.db.commit()

        # Trigger execution
        return self._trigger_execution(
            run=run, run_config=run_config, input_data=input_data
        )

    def launch_run(
        self,
        run: Run,
        input_data: dict,
        run_config_variables: dict[str, str] | None = None,
    ) -> Run:
        """
        Launch a run that has already been created.

        Args:
            run: Run object to launch
            input_data: Input data for the run
            run_config_variables: Optional configuration variables

        Returns:
            Launched Run object

        Raises:
            NotFoundException: If policy version not found
            VariablesNotSetException: If required variables are missing
            UnhandledException: If run launch fails
        """
        # Validate and prepare configuration
        run_config = self._prepare_run_config(
            run.policy_version_id, run.project_id, run_config_variables
        )

        # Trigger execution
        return self._trigger_execution(
            run=run, run_config=run_config, input_data=input_data
        )

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
        # Verify run exists
        self.run_loader.get_run(run_id, project_id=project_id)

        # Create metadata record
        meta = StepMetadata(
            run_id=run_id,
            step_name=metadata.step_name,
            node_type=metadata.node_type,
            start_time=metadata.start_time,
            end_time=metadata.end_time,
            error=metadata.error,
            extra=metadata.extra,
        )
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
        run = self.run_loader.get_run(run_id, project_id=project_id)

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

        # Trigger shadow runs if part of a run group
        # TODO: What to do when the main run fails?
        # TODO: Should we trigger the remaining runs with a subprocess (so we don't
        # halt the API's response)?
        if run.run_group_id:
            self.logger.debug(
                "launching_shadow_runs",
                run_group_id=str(run.run_group_id),
            )
            self._launch_pending_runs(run.run_group_id)

        return run

    def _launch_pending_runs(self, run_group_id: UUID) -> None:
        """
        Launch pending runs in a run group.

        Args:
            run_group_id: Run group UUID
        """
        # Get run group and input data
        run_group = self.db.query(RunGroup).filter_by(run_group_id=run_group_id).first()
        if not run_group:
            self.logger.error("run_group_not_found", run_group_id=str(run_group_id))
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
            self.logger.debug("launching_run", run_id=str(run.run_id))
            try:
                self.launch_run(run=run, input_data=input_data)
            except Exception as e:
                # TODO: Structure log to trace the run that failed and the way it was triggered
                self.logger.error(
                    "failed_to_launch_run",
                    run_id=str(run.run_id),
                    error=str(e),
                    exc_info=True,
                )
                continue

    def _prepare_run_config(
        self,
        policy_version_id: str,
        project_id: UUID | None,
        run_config_variables: dict[str, str] | None,
    ) -> RunConfig:
        """
        Validate policy version and resolve configuration variables.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID
            run_config_variables: Optional configuration variables

        Returns:
            RunConfig object

        Raises:
            NotFoundException: If policy version not found
            VariablesNotSetException: If required variables are missing
        """
        version = self.policy_version_loader.get_policy_version(
            policy_version_id,
            project_id=project_id,
        )
        if version is None:
            msg = f"Policy version {policy_version_id} not found"
            raise NotFoundException(msg)

        config_variables, missing = resolve_config_variables_from_id(
            db=self.db,
            policy_version_id=policy_version_id,
            required_variables=version.workflow.variables,
            run_config_variables=run_config_variables,
        )
        if len(missing) > 0:
            raise VariablesNotSetException(f"Mandatory variables not set: {missing}")

        return RunConfig(
            workflow_id=str(version.workflow_id), variables=config_variables
        )

    def _trigger_execution(
        self,
        run: Run,
        run_config: RunConfig,
        input_data: dict,
    ) -> Run:
        """
        Trigger run execution using the backend.

        Args:
            run: Run object
            run_config: RunConfig object
            input_data: Input data for the run

        Returns:
            Updated Run object with execution ID

        Raises:
            UnhandledException: If execution triggering fails
        """

        input_schema = self._get_input_schema(run_config.workflow_id)

        try:
            backend_run_id = self.backend.trigger_job(
                run_id=str(run.run_id),
                workflow_id=run_config.workflow_id,
                input_data=input_data,
                input_schema=input_schema,
                config_variables=run_config.variables,
                project_id=str(run.project_id) if run.project_id else None,
            )
            self.logger.debug(
                "triggered_job",
                run_id=str(run.run_id),
                backend_run_id=backend_run_id,
            )
            run.status = RunStatus.STARTED
            run.started_at = datetime.now(timezone.utc)
            run.backend_run_id = backend_run_id
            self.db.commit()
        except Exception as e:
            run.status = RunStatus.FAILURE
            self.db.commit()
            raise UnhandledException(f"Failed to launch run: {str(e)}")

        return run

    def _get_input_schema(self, workflow_id: str) -> dict[str, str]:
        workflow_def_json = (
            self.db.query(Workflow.spec)
            .where(Workflow.workflow_id == workflow_id)
            .scalar()
        )
        # While this can technically raise a validation error, it would
        # have occurred in the workflow creation.
        workflow_def = PolicyDefinitionDict.model_validate(workflow_def_json)
        return workflow_def.input_schema


MIN_POLLING_INTERVAL_MS = 500
MAX_POLLING_TIMEOUT_MS = 300000


async def get_run_result(
    db: Session, run_id: str, polling_interval_ms: int, polling_timeout_ms: int
) -> RunResult:
    """Poll the database for the run result.

    This is a blocking function that will wait for the run to complete
    or timeout after a certain period.
    """

    def clip(value):
        return max(min(value, MAX_POLLING_TIMEOUT_MS), MIN_POLLING_INTERVAL_MS)

    elapsed = 0
    completed = False
    run_obj: Run | None = None

    polling_interval = clip(polling_interval_ms) / 1000
    polling_timeout = clip(polling_timeout_ms) / 1000

    while elapsed < polling_timeout:
        if run_obj:
            # Clear the database cache to ensure we get the latest run status
            db.expire(run_obj)

        run_obj = db.execute(select(Run).where(Run.run_id == run_id)).scalars().first()
        if run_obj.status in (RunStatus.SUCCESS, RunStatus.FAILURE):
            completed = True
            break

        await asyncio.sleep(polling_interval)
        elapsed += polling_interval

    if not completed:
        raise RunPollingTimeoutException(
            f"Run {run_id} timed out after {polling_timeout} seconds. "
            "Check the run logs for more details."
        )

    return RunResult(
        run_id=run_obj.run_id,
        status=run_obj.status,
        result=run_obj.result,
        run_metadata=run_obj.run_metadata,
    )
