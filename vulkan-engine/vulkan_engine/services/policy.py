"""
Policy management service.

Handles all business logic related to policies including CRUD operations,
validation, and allocation strategy management.
"""

from datetime import date

import pandas as pd
from sqlalchemy import func as F
from sqlalchemy import select

from vulkan.core.run import RunStatus
from vulkan_engine.db import Policy, PolicyVersion, PolicyVersionStatus, Run
from vulkan_engine.events import VulkanEvent
from vulkan_engine.exceptions import (
    InvalidAllocationStrategyException,
    InvalidPolicyVersionException,
    PolicyHasVersionsException,
    PolicyNotFoundException,
    PolicyVersionNotFoundException,
)
from vulkan_engine.schemas import PolicyAllocationStrategy, PolicyBase, PolicyCreate
from vulkan_engine.services.base import BaseService
from vulkan_engine.utils import validate_date_range


class PolicyService(BaseService):
    """Service for managing policies and their operations."""

    def list_policies(self, include_archived: bool = False) -> list[Policy]:
        """
        List all policies.

        Args:
            include_archived: Whether to include archived policies

        Returns:
            List of Policy objects
        """
        filters = {}
        if not include_archived:
            filters["archived"] = False

        return self.db.query(Policy).filter_by(**filters).all()

    def create_policy(self, policy_data: PolicyCreate) -> Policy:
        """
        Create a new policy.

        Args:
            policy_data: Policy creation data

        Returns:
            Created Policy object
        """
        policy = Policy(**policy_data.model_dump())
        self.db.add(policy)
        self.db.commit()

        self._log_event(
            VulkanEvent.POLICY_CREATED,
            policy_id=policy.policy_id,
            **policy_data.model_dump(),
        )

        return policy

    def get_policy(self, policy_id: str) -> Policy:
        """
        Get a policy by ID.

        Args:
            policy_id: Policy UUID

        Returns:
            Policy object

        Raises:
            PolicyNotFoundException: If policy doesn't exist
        """
        policy = self.db.query(Policy).filter_by(policy_id=policy_id).first()

        if not policy:
            raise PolicyNotFoundException(f"Policy {policy_id} not found")

        return policy

    def update_policy(self, policy_id: str, update_data: PolicyBase) -> Policy:
        """
        Update a policy.

        Args:
            policy_id: Policy UUID
            update_data: Update data

        Returns:
            Updated Policy object

        Raises:
            PolicyNotFoundException: If policy doesn't exist
            InvalidAllocationStrategyException: If allocation strategy is invalid
        """
        policy = self.get_policy(policy_id)

        # Validate allocation strategy if provided
        if update_data.allocation_strategy:
            self._validate_allocation_strategy(update_data.allocation_strategy)
            policy.allocation_strategy = update_data.allocation_strategy.model_dump()

        # Update fields if provided
        if update_data.name is not None and update_data.name != policy.name:
            policy.name = update_data.name

        if (
            update_data.description is not None
            and update_data.description != policy.description
        ):
            policy.description = update_data.description

        self.db.commit()

        self._log_event(
            VulkanEvent.POLICY_UPDATED, policy_id=policy_id, **update_data.model_dump()
        )

        return policy

    def delete_policy(self, policy_id: str) -> None:
        """
        Delete (archive) a policy.

        Args:
            policy_id: Policy UUID

        Raises:
            PolicyNotFoundException: If policy doesn't exist or already archived
            PolicyHasVersionsException: If policy has active versions
        """
        policy = self.db.query(Policy).filter_by(policy_id=policy_id).first()

        if not policy or policy.archived:
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

        self._log_event(VulkanEvent.POLICY_DELETED, policy_id=policy_id)

    def list_policy_versions(
        self, policy_id: str, include_archived: bool = False
    ) -> list[PolicyVersion]:
        """
        List versions for a policy.

        Args:
            policy_id: Policy UUID
            include_archived: Whether to include archived versions

        Returns:
            List of PolicyVersion objects
        """
        filters = {"policy_id": policy_id}
        if not include_archived:
            filters["archived"] = False

        return (
            self.db.query(PolicyVersion)
            .filter_by(**filters)
            .order_by(PolicyVersion.created_at.asc())
            .all()
        )

    def list_runs_by_policy(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
    ) -> list[Run]:
        """
        List runs for a policy within a date range.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter

        Returns:
            List of Run objects
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        query = (
            select(Run)
            .join(PolicyVersion)
            .filter(
                (PolicyVersion.policy_id == policy_id)
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .order_by(Run.created_at.desc())
        )

        return self.db.execute(query).scalars().all()

    def get_run_duration_stats(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Get run duration statistics for a policy.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs

        Returns:
            List of duration statistics by date
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id
            )

        duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
        date_clause = F.DATE(Run.created_at).label("date")

        query = (
            select(
                date_clause,
                F.avg(duration_seconds).label("avg_duration"),
                F.min(duration_seconds).label("min_duration"),
                F.max(duration_seconds).label("max_duration"),
            )
            .where(
                (Run.policy_version_id.in_(version_ids))
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .group_by(date_clause)
        )

        df = pd.read_sql(query, self.db.bind)
        return df.to_dict(orient="records")

    def get_run_duration_by_status(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Get run duration statistics grouped by status.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs

        Returns:
            List of duration statistics by date and status
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id
            )

        duration_seconds = F.extract("epoch", Run.last_updated_at - Run.created_at)
        date_clause = F.DATE(Run.created_at).label("date")

        query = (
            select(
                date_clause,
                Run.status,
                F.avg(duration_seconds).label("avg_duration"),
            )
            .where(
                (Run.policy_version_id.in_(version_ids))
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .group_by(date_clause, Run.status)
        )

        df = pd.read_sql(query, self.db.bind)
        df = df.pivot(
            index=date_clause.name, values="avg_duration", columns=["status"]
        ).reset_index()

        return df.to_dict(orient="records")

    def get_run_counts(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Get run counts and error rates for a policy.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs

        Returns:
            List of run counts and error rates by date
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id
            )

        date_clause = F.DATE(Run.created_at).label("date")

        query = (
            select(
                date_clause,
                F.count(Run.run_id).label("count"),
                (
                    100
                    * F.count(Run.run_id).filter(Run.status == RunStatus.FAILURE)
                    / F.count(Run.run_id)
                ).label("error_rate"),
            )
            .where(
                (Run.policy_version_id.in_(version_ids))
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .group_by(date_clause)
        )

        df = pd.read_sql(query, self.db.bind)
        return df.to_dict(orient="records")

    def get_run_outcomes(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
    ) -> list[dict]:
        """
        Get run outcome distribution for a policy.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs

        Returns:
            List of run outcomes by date
        """
        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id
            )

        date_clause = F.DATE(Run.created_at).label("date")

        # Subquery for totals
        subquery = (
            select(date_clause, F.count(Run.run_id).label("total"))
            .where(
                (Run.policy_version_id.in_(version_ids))
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .group_by(date_clause)
            .subquery()
        )

        # Main query
        query = (
            select(
                date_clause,
                Run.result.label("result"),
                F.count(Run.run_id).label("count"),
                subquery.c.total.label("total"),
            )
            .join(subquery, onclause=subquery.c.date == date_clause)
            .where(
                (Run.policy_version_id.in_(version_ids))
                & (Run.created_at >= start_date)
                & (F.DATE(Run.created_at) <= end_date)
            )
            .group_by(date_clause, Run.result, subquery.c.total)
        )

        df = pd.read_sql(query, self.db.bind)
        df["percentage"] = 100 * df["count"] / df["total"]
        df = (
            df.pivot(
                index=date_clause.name,
                values=["count", "percentage"],
                columns=["result"],
            )
            .reset_index()
            .fillna(0)
        )

        return df.to_dict(orient="records")

    def _validate_allocation_strategy(
        self, allocation_strategy: PolicyAllocationStrategy
    ) -> None:
        """
        Validate an allocation strategy.

        Args:
            allocation_strategy: Strategy to validate

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
                self._validate_policy_version_id(version_id)

        # Validate choice versions
        for option in allocation_strategy.choice:
            self._validate_policy_version_id(option.policy_version_id)

        # TODO: Validate if schemas are compatible
        # TODO: Validate if config_variables are compatible

    def _validate_policy_version_id(self, policy_version_id: str) -> PolicyVersion:
        """
        Validate a policy version exists and is valid.

        Args:
            policy_version_id: Version UUID to validate

        Returns:
            PolicyVersion object

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist
            InvalidPolicyVersionException: If version is not valid
        """
        version = (
            self.db.query(PolicyVersion)
            .filter_by(policy_version_id=policy_version_id)
            .first()
        )

        if not version:
            raise PolicyVersionNotFoundException(
                f"Policy version {policy_version_id} not found"
            )

        if version.status != PolicyVersionStatus.VALID:
            raise InvalidPolicyVersionException(
                f"Policy version {policy_version_id} is not valid"
            )

        return version
