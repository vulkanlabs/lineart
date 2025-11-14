"""
Policy analytics and metrics service.

Handles all analytics operations related to policies including run duration statistics,
run counts, error rates, and outcome distribution analysis.
"""

from datetime import date

import pandas as pd
from sqlalchemy import func as F
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from vulkan.core.run import RunStatus

from vulkan_engine.db import PolicyVersion, Run
from vulkan_engine.loaders import PolicyLoader
from vulkan_engine.services.analytics_utils import query_to_dataframe
from vulkan_engine.services.base import BaseService
from vulkan_engine.utils import validate_date_range


class PolicyAnalyticsService(BaseService):
    """Service for policy analytics and metrics."""

    def __init__(self, db: AsyncSession):
        """
        Initialize policy analytics service.

        Args:
            db: Database session
        """
        super().__init__(db)
        self.policy_loader = PolicyLoader(db)

    async def get_run_duration_stats(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
        project_id: str = None,
    ) -> list[dict]:
        """
        Get run duration statistics for a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs
            project_id: Optional project UUID to filter by

        Returns:
            List of duration statistics by date
        """
        # Validate policy exists
        await self.policy_loader.get_policy(policy_id, project_id=project_id)

        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids_stmt = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.project_id == project_id,
            )
            version_ids_result = await self.db.execute(version_ids_stmt)
            version_ids = list(version_ids_result.scalars().all())

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

        df = await query_to_dataframe(self.db, query)
        return df.to_dict(orient="records")

    async def get_run_duration_by_status(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
        project_id: str = None,
    ) -> list[dict]:
        """
        Get run duration statistics grouped by status, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs
            project_id: Optional project UUID to filter by

        Returns:
            List of duration statistics by date and status
        """
        # Validate policy exists
        await self.policy_loader.get_policy(policy_id, project_id=project_id)

        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids_stmt = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.project_id == project_id,
            )
            version_ids_result = await self.db.execute(version_ids_stmt)
            version_ids = list(version_ids_result.scalars().all())

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

        df = await query_to_dataframe(self.db, query)
        df = df.pivot(
            index=date_clause.name, values="avg_duration", columns=["status"]
        ).reset_index()

        return df.to_dict(orient="records")

    async def get_run_counts(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
        project_id: str = None,
    ) -> list[dict]:
        """
        Get run counts and error rates for a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs
            project_id: Optional project UUID to filter by

        Returns:
            List of run counts and error rates by date
        """
        # Validate policy exists
        await self.policy_loader.get_policy(policy_id, project_id=project_id)

        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids_stmt = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.project_id == project_id,
            )
            version_ids_result = await self.db.execute(version_ids_stmt)
            version_ids = list(version_ids_result.scalars().all())

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

        df = await query_to_dataframe(self.db, query)
        return df.to_dict(orient="records")

    async def get_run_outcomes(
        self,
        policy_id: str,
        start_date: date | None = None,
        end_date: date | None = None,
        version_ids: list[str] | None = None,
        project_id: str = None,
    ) -> list[dict]:
        """
        Get run outcome distribution for a policy, optionally filtered by project.

        Args:
            policy_id: Policy UUID
            start_date: Start date filter
            end_date: End date filter
            version_ids: Optional list of specific version IDs
            project_id: Optional project UUID to filter by

        Returns:
            List of run outcomes by date
        """
        # Validate policy exists
        await self.policy_loader.get_policy(policy_id, project_id=project_id)

        start_date, end_date = validate_date_range(start_date, end_date)

        if version_ids is None:
            version_ids_stmt = select(PolicyVersion.policy_version_id).where(
                PolicyVersion.policy_id == policy_id,
                PolicyVersion.project_id == project_id,
            )
            version_ids_result = await self.db.execute(version_ids_stmt)
            version_ids = list(version_ids_result.scalars().all())

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

        df = await query_to_dataframe(self.db, query)
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
