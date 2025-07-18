"""
Run allocation service.

Handles run group creation and allocation based on policy strategies.
"""

from typing import Dict

from vulkan_engine.dagster.launch_run import DagsterRunLauncher, allocate_runs
from vulkan_engine.db import RunGroup
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
)
from vulkan_engine.loaders import PolicyLoader
from vulkan_engine.schemas import PolicyAllocationStrategy
from vulkan_engine.services.base import BaseService
from vulkan_engine.validators import validate_uuid, validate_optional_uuid


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
        self.policy_loader = PolicyLoader(db)

    def create_run_group(
        self,
        policy_id: str,
        input_data: Dict,
        config_variables: Dict,
        project_id: str = None,
    ) -> Dict:
        """
        Create a run group and allocate runs based on policy strategy.

        Args:
            policy_id: Policy UUID
            input_data: Input data for runs
            config_variables: Configuration variables
            project_id: Optional project UUID to filter by

        Returns:
            Dictionary with policy_id, run_group_id, and allocated runs

        Raises:
            PolicyNotFoundException: If policy doesn't exist or doesn't belong to specified project
            InvalidAllocationStrategyException: If policy has no allocation strategy
        """
        # Validate policy ID
        validate_uuid(policy_id, "policy")

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
        with self.db.begin():
            self.db.add(run_group)

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
            project_id=policy.project_id,
        )

        return {
            "policy_id": policy.policy_id,
            "run_group_id": run_group.run_group_id,
            "runs": runs,
        }
