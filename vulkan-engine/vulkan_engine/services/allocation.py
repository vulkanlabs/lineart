"""
Run allocation service.

Handles run group creation and allocation based on policy strategies.
"""

from typing import Dict

import sqlalchemy.exc

from vulkan_engine.dagster.launch_run import DagsterRunLauncher, allocate_runs
from vulkan_engine.db import Policy, RunGroup
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
    PolicyNotFoundException,
)
from vulkan_engine.schemas import PolicyAllocationStrategy
from vulkan_engine.services.base import BaseService


class AllocationService(BaseService):
    """Service for managing run allocation and run groups."""

    def __init__(self, db, launcher: DagsterRunLauncher, logger=None):
        """
        Initialize allocation service.

        Args:
            db: Database session
            launcher: Dagster run launcher
            logger: Optional logger
        """
        super().__init__(db, logger)
        self.launcher = launcher

    def create_run_group(
        self, policy_id: str, input_data: Dict, config_variables: Dict
    ) -> Dict:
        """
        Create a run group and allocate runs based on policy strategy.

        Args:
            policy_id: Policy UUID
            input_data: Input data for runs
            config_variables: Configuration variables

        Returns:
            Dictionary with policy_id, run_group_id, and allocated runs

        Raises:
            PolicyNotFoundException: If policy doesn't exist
            InvalidAllocationStrategyException: If policy has no allocation strategy
        """
        try:
            policy = self.db.query(Policy).filter_by(policy_id=policy_id).first()
        except sqlalchemy.exc.DataError:
            raise PolicyNotFoundException(f"Invalid policy_id: {policy_id}")

        if not policy:
            raise PolicyNotFoundException(f"Policy {policy_id} not found")

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

        if self.logger:
            self.logger.system.info(
                f"Allocating runs with input_data {input_data}",
                extra={"extra": {"policy_id": policy_id}},
            )

        # Allocate runs
        runs = allocate_runs(
            db=self.db,
            launcher=self.launcher,
            input_data=input_data,
            run_group_id=run_group.run_group_id,
            allocation_strategy=strategy,
        )

        return {
            "policy_id": policy.policy_id,
            "run_group_id": run_group.run_group_id,
            "runs": runs,
        }
