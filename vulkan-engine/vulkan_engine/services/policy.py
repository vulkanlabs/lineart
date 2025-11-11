"""
Policy management service.

Handles all business logic related to policies including CRUD operations,
validation, and allocation strategy management.
"""

from datetime import date

from sqlalchemy import func as F
from sqlalchemy import select

from vulkan_engine.db import Policy, PolicyVersion, Run, WorkflowStatus
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
    InvalidPolicyVersionException,
    PolicyHasVersionsException,
    PolicyNotFoundException,
    PolicyVersionNotFoundException,
)
from vulkan_engine.loaders import PolicyLoader, PolicyVersionLoader
from vulkan_engine.schemas import PolicyAllocationStrategy, PolicyBase, PolicyCreate
from vulkan_engine.services.base import BaseService
from vulkan_engine.utils import validate_date_range


class PolicyService(BaseService):
    """Service for managing policies and their operations."""

    def __init__(self, db):
        """
        Initialize policy service.

        Args:
            db: Database session
        """
        super().__init__(db)
        self.policy_loader = PolicyLoader(db)
        self.policy_version_loader = PolicyVersionLoader(db)

    def list_policies(
        self, include_archived: bool = False, project_id: str = None
    ) -> list[Policy]:
        """
        List policies, optionally filtered by project.

        Args:
            include_archived: Whether to include archived policies
            project_id: Optional project UUID to filter by

        Returns:
            List of Policy objects
        """
        return self.policy_loader.list_policies(
            project_id=project_id, include_archived=include_archived
        )

    def create_policy(
        self, policy_data: PolicyCreate, project_id: str = None
    ) -> Policy:
        """
        Create a new policy.

        Args:
            policy_data: Policy creation data
            project_id: Optional project UUID to associate with

        Returns:
            Created Policy object
        """
        policy_dict = policy_data.model_dump()
        policy_dict["project_id"] = project_id

        policy = Policy(**policy_dict)
        self.db.add(policy)
        self.db.commit()

        return policy

    def get_policy(self, policy_id: str, project_id: str = None) -> Policy:
        """
        Get a policy by ID, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            project_id: Optional project UUID to filter by

        Returns:
            Policy object

        Raises:
            PolicyNotFoundException: If policy doesn't exist or doesn't belong to specified project
        """
        return self.policy_loader.get_policy(policy_id, project_id=project_id)

    def update_policy(
        self, policy_id: str, update_data: PolicyBase, project_id: str = None
    ) -> Policy:
        """
        Update a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            update_data: Update data
            project_id: Optional project UUID to filter by

        Returns:
            Updated Policy object

        Raises:
            PolicyNotFoundException: If policy doesn't exist or doesn't belong to specified project
            InvalidAllocationStrategyException: If allocation strategy is invalid
        """
        policy = self.policy_loader.get_policy(policy_id, project_id=project_id)

        # Validate allocation strategy if provided
        if update_data.allocation_strategy:
            self._validate_allocation_strategy(
                update_data.allocation_strategy, project_id=project_id
            )
            policy.allocation_strategy = update_data.allocation_strategy.model_dump()
        else:
            policy.allocation_strategy = None

        # Update fields if provided
        if update_data.name is not None and update_data.name != policy.name:
            policy.name = update_data.name

        if (
            update_data.description is not None
            and update_data.description != policy.description
        ):
            policy.description = update_data.description

        self.db.commit()

        return policy

    def delete_policy(self, policy_id: str, project_id: str = None) -> None:
        """
        Delete (archive) a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            project_id: Optional project UUID to filter by

        Raises:
            PolicyNotFoundException: If policy doesn't exist, already archived, or doesn't belong to specified project
            PolicyHasVersionsException: If policy has active versions
        """
        policy = self.policy_loader.get_policy(policy_id, project_id=project_id)

        if policy.archived:
            raise PolicyNotFoundException(f"Policy {policy_id} not found")

        # Check for active versions
        active_versions_count = (
            self.db.query(PolicyVersion)
            .filter_by(policy_id=policy_id, archived=False)
            .count()
        )

        if active_versions_count > 0:
            raise PolicyHasVersionsException(
                f"Policy {policy_id} has {active_versions_count} active versions, "
                "delete them first"
            )

        policy.archived = True
        self.db.commit()

    def list_policy_versions(
        self, policy_id: str, include_archived: bool = False, project_id: str = None
    ) -> list[PolicyVersion]:
        """
        List versions for a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            include_archived: Whether to include archived versions
            project_id: Optional project UUID to filter by

        Returns:
            List of PolicyVersion objects
        """
        return self.policy_version_loader.list_policy_versions(
            policy_id=policy_id,
            project_id=project_id,
            include_archived=include_archived,
        )

    def list_runs_by_policy(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        project_id: str = None,
    ) -> list[Run]:
        """
        List runs for a policy within a date range, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            project_id: Optional project UUID to filter by

        Returns:
            List of Run objects
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        query = (
            select(Run)
            .join(PolicyVersion)
            .filter(
                (PolicyVersion.policy_id == policy_id)
                & (PolicyVersion.project_id == project_id)
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .order_by(Run.created_at.desc())
        )

        return self.db.execute(query).scalars().all()

    def _validate_allocation_strategy(
        self, allocation_strategy: PolicyAllocationStrategy, project_id: str = None
    ) -> None:
        """
        Validate an allocation strategy.

        Args:
            allocation_strategy: Strategy to validate
            project_id: Optional project UUID to filter by

        Raises:
            InvalidAllocationStrategyException: If strategy is invalid
        """
        if not allocation_strategy:
            return

        if len(allocation_strategy.choice) == 0:
            raise InvalidAllocationStrategyException(
                "Allocation strategy must have at least one option"
            )

        total_frequency = sum(option.frequency for option in allocation_strategy.choice)
        if total_frequency != 1000:
            raise InvalidAllocationStrategyException(
                "The sum of frequencies must be 1000"
            )

        # Validate shadow versions if present
        if allocation_strategy.shadow:
            for version_id in allocation_strategy.shadow:
                self._validate_policy_version_id(version_id, project_id)

        # Validate choice versions
        for option in allocation_strategy.choice:
            self._validate_policy_version_id(option.policy_version_id, project_id)

        # TODO: Validate if schemas are compatible
        # TODO: Validate if config_variables are compatible

    def _validate_policy_version_id(
        self, policy_version_id: str, project_id: str = None
    ) -> PolicyVersion:
        """
        Validate a policy version exists and is valid.

        Args:
            policy_version_id: Version UUID to validate
            project_id: Optional project UUID to filter by

        Returns:
            PolicyVersion object

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
            InvalidPolicyVersionException: If version is not valid
        """
        version = self.policy_version_loader.get_policy_version(
            policy_version_id, project_id=project_id
        )

        if not version:
            raise PolicyVersionNotFoundException(
                f"Policy version {policy_version_id} not found"
            )

        if version.workflow.status != WorkflowStatus.VALID:
            raise InvalidPolicyVersionException(
                f"Policy version {policy_version_id} is not valid"
            )

        return version
