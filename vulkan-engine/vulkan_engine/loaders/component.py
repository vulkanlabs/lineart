"""
Component loader for data access layer.
"""

from vulkan_engine.db import Component
from vulkan_engine.exceptions import ComponentNotFoundException
from vulkan_engine.loaders.base import BaseLoader


class ComponentLoader(BaseLoader):
    """Loader for Component resources."""

    def list_components(
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
        query = self.db.query(Component).filter(Component.project_id == project_id)

        query = self._apply_archived_filter(query, include_archived)

        return query.all()

    def get_component(
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
        query = self.db.query(Component).filter(
            Component.name == name,
            Component.project_id == project_id,
        )

        query = self._apply_archived_filter(query, include_archived)

        component = query.first()
        if not component:
            raise ComponentNotFoundException(f"Component {name} not found")

        return component
