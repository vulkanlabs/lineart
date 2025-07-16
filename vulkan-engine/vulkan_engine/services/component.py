"""
Component service.

Handles business logic for component operations.
"""

from typing import List
from uuid import UUID

from sqlalchemy.orm import Session

from vulkan_engine import schemas
from vulkan_engine.db import Component
from vulkan_engine.events import VulkanEvent
from vulkan_engine.exceptions import ComponentNotFoundException


class ComponentService:
    """Service for component operations."""

    def __init__(self, db: Session):
        self.db = db

    def list_components(
        self, include_archived: bool = False
    ) -> List[schemas.Component]:
        """List all components."""
        query = self.db.query(Component)
        if not include_archived:
            query = query.filter(Component.archived == False)  # noqa: E712
        components = query.all()
        return [schemas.Component.model_validate(component) for component in components]

    def get_component(self, component_id: UUID) -> schemas.Component:
        """Get a component by ID."""
        component = (
            self.db.query(Component)
            .filter(Component.component_id == component_id)
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")
        return schemas.Component.model_validate(component)

    def create_component(self, config: schemas.ComponentBase) -> schemas.Component:
        """Create a new component."""
        component = Component(
            name=config.name,
            description=config.description,
            icon=config.icon,
            requirements=config.requirements,
            spec=config.spec,
            input_schema=config.input_schema,
            variables=config.variables,
            ui_metadata=config.ui_metadata,
        )
        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        self._log_event(
            VulkanEvent.COMPONENT_CREATED, component_id=component.component_id
        )
        return schemas.Component.model_validate(component)

    def update_component(
        self, component_id: UUID, config: schemas.ComponentBase
    ) -> schemas.Component:
        """Update a component."""
        component = (
            self.db.query(Component)
            .filter(Component.component_id == component_id)
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")

        if config.name is not None:
            component.name = config.name
        if config.description is not None:
            component.description = config.description
        if config.icon is not None:
            component.icon = config.icon

        self.db.commit()
        self.db.refresh(component)
        self._log_event(
            VulkanEvent.COMPONENT_UPDATED, component_id=component.component_id
        )
        return schemas.Component.model_validate(component)

    def delete_component(self, component_id: UUID) -> None:
        """Delete (archive) a component."""
        component = (
            self.db.query(Component)
            .filter(Component.component_id == component_id)
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")

        component.archived = True
        self.db.commit()
        self._log_event(VulkanEvent.COMPONENT_DELETED, component_id=component_id)
