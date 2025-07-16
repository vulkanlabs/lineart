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
from vulkan_engine.logger import VulkanLogger
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.workflow import WorkflowService


class ComponentService(BaseService):
    """Service for component operations."""

    def __init__(self, db: Session, logger: VulkanLogger | None = None):
        super().__init__(db, logger)
        self.workflow_service = WorkflowService(db, logger)

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

        # Fill in defaults for non-nullable fields
        requirements = config.requirements or []
        variables = config.variables or []
        spec = config.spec or {"nodes": [], "input_schema": {}}
        input_schema = config.input_schema or {}

        # Create workflow for the component
        workflow = self.workflow_service.create_workflow(
            spec=spec,
            input_schema=input_schema,
            requirements=requirements,
            variables=variables,
            ui_metadata=config.ui_metadata or {},
        )

        component = Component(
            name=config.name,
            description=config.description,
            icon=config.icon,
            workflow_id=workflow.workflow_id,
        )

        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        self._log_event(
            VulkanEvent.COMPONENT_CREATED, component_id=component.component_id
        )
        return schemas.Component.from_orm(component, workflow)

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

        # Update component fields
        if config.name is not None:
            component.name = config.name
        if config.description is not None:
            component.description = config.description
        if config.icon is not None:
            component.icon = config.icon

        # Update the underlying workflow
        if any(
            [
                config.spec is not None,
                config.input_schema is not None,
                config.requirements is not None,
                config.variables is not None,
                config.ui_metadata is not None,
            ]
        ):
            self.workflow_service.update_workflow(
                workflow_id=component.workflow_id,
                spec=config.spec,
                input_schema=config.input_schema,
                requirements=config.requirements,
                variables=config.variables,
                ui_metadata=config.ui_metadata,
            )

        self.db.commit()
        self.db.refresh(component)

        workflow = self.workflow_service.update_workflow(
            workflow_id=component.workflow_id,
            spec=config.spec,
            input_schema=config.input_schema,
            requirements=config.requirements,
            variables=config.variables,
            ui_metadata=config.ui_metadata,
        )

        self._log_event(
            VulkanEvent.COMPONENT_UPDATED, component_id=component.component_id
        )
        return schemas.Component.from_orm(component, workflow)

    def delete_component(self, component_id: UUID) -> None:
        """Delete (archive) a component."""
        component = (
            self.db.query(Component)
            .filter(Component.component_id == component_id)
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")

        # Delete the underlying workflow
        if component.workflow_id:
            self.workflow_service.delete_workflow(component.workflow_id)

        component.archived = True
        self.db.commit()
        self._log_event(VulkanEvent.COMPONENT_DELETED, component_id=component_id)
