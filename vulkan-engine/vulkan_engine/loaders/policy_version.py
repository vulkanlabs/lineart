"""
PolicyVersion loader for data access layer.
"""

from sqlalchemy import select

from vulkan_engine.db import PolicyVersion
from vulkan_engine.exceptions import PolicyVersionNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class PolicyVersionLoader(BaseLoader):
    """Loader for PolicyVersion resources."""

    async def get_policy_version(
        self,
        policy_version_id: str,
        project_id: str = None,
        include_archived: bool = True,
    ) -> PolicyVersion:
        """
        Get a policy version by ID, optionally filtered by project.

        Args:
            policy_version_id: Policy version UUID
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived versions (default: True)

        Returns:
            PolicyVersion object

        Raises:
            PolicyVersionNotFoundException: If version doesn't exist or doesn't belong to specified project
        """
        stmt = select(PolicyVersion).filter(
            PolicyVersion.policy_version_id == policy_version_id,
            PolicyVersion.project_id == project_id,
        )

        stmt = self._apply_archived_filter(stmt, include_archived)

        result = await self.db.execute(stmt)
        version = result.scalar_one_or_none()
        if not version:
            raise PolicyVersionNotFoundException(
                f"Policy version {policy_version_id} not found"
            )

        return version

    async def list_policy_versions(
        self,
        policy_id: str = None,
        project_id: str = None,
        include_archived: bool = False,
    ) -> list[PolicyVersion]:
        """
        List policy versions with optional filtering.

        Args:
            policy_id: Optional policy ID to filter by
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived versions

        Returns:
            List of PolicyVersion objects
        """
        stmt = select(PolicyVersion).filter(PolicyVersion.project_id == project_id)

        if policy_id:
            stmt = stmt.filter(PolicyVersion.policy_id == policy_id)

        stmt = self._apply_archived_filter(stmt, include_archived)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())
