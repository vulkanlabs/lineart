"""
Component loader for data access layer.
"""

from sqlalchemy import select

from vulkan_engine.db import Component
from vulkan_engine.exceptions import ComponentNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class ComponentLoader(BaseLoader):
    """Loader for Component resources."""

    async def list_components(
        self,
        project_id: str = None,
        include_archived: bool = False,
    ) -> list[Component]:
        """
        List components with optional filtering.

        Args:
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived components

        Returns:
            List of Component objects
        """
        stmt = select(Component).filter(Component.project_id == project_id)

        stmt = self._apply_archived_filter(stmt, include_archived)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_component(
        self,
        name: str,
        project_id: str = None,
        include_archived: bool = True,
    ) -> Component:
        """
        Get a component by name, optionally filtered by project.
        Args:
            name: Component name
            project_id: Optional project UUID to filter by
            include_archived: Whether to include archived components (default: True)
        Returns:
            Component object
        Raises:
            ComponentNotFoundException: If component doesn't exist or doesn't belong to specified project
        """
        stmt = select(Component).filter(
            Component.name == name,
            Component.project_id == project_id,
        )

        stmt = self._apply_archived_filter(stmt, include_archived)

        result = await self.db.execute(stmt)
        component = result.scalar_one_or_none()
        if not component:
            raise ComponentNotFoundException(f"Component {name} not found")

        return component
