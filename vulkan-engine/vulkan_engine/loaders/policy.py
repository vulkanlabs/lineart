"""
Policy loader for data access layer.
"""

from typing import List

from vulkan_engine.db import Policy
from vulkan_engine.exceptions import PolicyNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class PolicyLoader(BaseLoader):
    """Loader for Policy resources."""

    def get_policy(self, policy_id: str, project_id: str = None) -> Policy:
        """
        Get a policy by ID, filtered by project.

        Args:
            policy_id: Policy UUID
            project_id: Optional project UUID to filter by

        Returns:
            Policy object

        Raises:
            PolicyNotFoundException: If policy doesn't exist or doesn't belong to specified project
        """
        policy = (
            self.db.query(Policy)
            .filter(Policy.policy_id == policy_id, Policy.project_id == project_id)
            .first()
        )

        if not policy:
            raise PolicyNotFoundException(f"Policy {policy_id} not found")

        return policy

    def list_policies(
        self, project_id: str = None, include_archived: bool = False
    ) -> List[Policy]:
        """
        List policies with optional filtering.

        Args:
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived policies

        Returns:
            List of Policy objects
        """
        query = self.db.query(Policy).filter(Policy.project_id == project_id)
        query = self._apply_archived_filter(query, include_archived)

        return query.all()
