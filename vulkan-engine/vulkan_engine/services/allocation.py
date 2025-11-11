"""
Run allocation service.

Handles run group creation and allocation based on policy strategies.
"""

from uuid import UUID

from numpy.random import choice
from sqlalchemy.orm import Session
from vulkan.core.run import RunStatus

from vulkan_engine.db import Run, RunGroup
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
)
from vulkan_engine.loaders import PolicyLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import (
    PolicyAllocationStrategy,
    RunGroupResult,
    RunGroupRuns,
)
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.run_orchestration import RunOrchestrationService


class AllocationService(BaseService):
    """Service for managing run allocation and run groups."""

    def __init__(self, db: Session, orchestrator: RunOrchestrationService):
        """
        Initialize allocation service.

        Args:
            db: Database session
            orchestrator: Run orchestration service
        """
        super().__init__(db)
        self.orchestrator = orchestrator
        self.policy_loader = PolicyLoader(db)
        self.logger = get_logger(__name__)

    def create_run_group(
        self,
        policy_id: str,
        input_data: dict,
        config_variables: dict,
        project_id: str = None,
    ) -> RunGroupResult:
        """
        Create a run group and allocate runs based on policy strategy.

        Args:
            policy_id: Policy UUID
            input_data: Input data for runs
            config_variables: Configuration variables
            project_id: Optional project UUID to filter by

        Returns:
            RunGroupResult

        Raises:
            PolicyNotFoundException: If policy doesn't exist or doesn't belong to specified project
            InvalidAllocationStrategyException: If policy has no allocation strategy
        """
        policy = self.policy_loader.get_policy(policy_id, project_id=project_id)

        if not policy.allocation_strategy:
            raise InvalidAllocationStrategyException(
                f"Policy {policy_id} has no allocation strategy"
            )

        # Create run group
        run_group = RunGroup(
            policy_id=policy_id,
            input_data=input_data,
        )
        self.db.add(run_group)
        self.db.commit()

        # Parse allocation strategy
        strategy = PolicyAllocationStrategy.model_validate(policy.allocation_strategy)

        self.logger.info(
            "allocating_runs",
            input_data=input_data,
            policy_id=policy_id,
        )

        # Allocate runs
        runs = self.allocate_runs(
            input_data=input_data,
            run_group_id=run_group.run_group_id,
            allocation_strategy=strategy,
            project_id=policy.project_id,
        )

        return RunGroupResult(
            policy_id=policy.policy_id,
            run_group_id=run_group.run_group_id,
            runs=runs,
        )

    def allocate_runs(
        self,
        input_data: dict,
        run_group_id: UUID,
        allocation_strategy: PolicyAllocationStrategy,
        project_id: UUID | None = None,
    ) -> RunGroupRuns:
        """
        Allocate runs based on the allocation strategy.

        Creates shadow runs if specified and selects a main run based on
        the choice strategy with probability weights.

        Args:
            input_data: Input data for runs
            run_group_id: Run group UUID
            allocation_strategy: Policy allocation strategy
            project_id: Optional project UUID

        Returns:
            RunGroupRuns with main and shadow run IDs
        """
        shadow = []

        # Create shadow runs if specified
        if allocation_strategy.shadow is not None:
            with self.db.begin():
                for policy_version_id in allocation_strategy.shadow:
                    run = Run(
                        policy_version_id=policy_version_id,
                        status=RunStatus.PENDING,
                        input_data=input_data,
                        run_group_id=run_group_id,
                        project_id=project_id,
                    )
                    self.db.add(run)
                    shadow.append(run.run_id)

        # Select main run based on choice strategy
        opts = [opt.policy_version_id for opt in allocation_strategy.choice]
        freq = [opt.frequency / 1000 for opt in allocation_strategy.choice]
        policy_version_id = choice(opts, p=freq)

        # Create and launch main run
        main = self.orchestrator.create_run(
            input_data=input_data,
            run_group_id=run_group_id,
            policy_version_id=policy_version_id,
            project_id=project_id,
        )
        return RunGroupRuns(main=main.run_id, shadow=shadow)
