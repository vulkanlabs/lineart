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

    def __init__(
        self,
        db: Session,
        workflow_service: WorkflowService,
        logger: VulkanLogger | None = None,
    ):
        super().__init__(db, logger)
        self.workflow_service = workflow_service

    def list_components(
        self,
        include_archived: bool = False,
        project_id: str | None = None,
    ) -> List[schemas.Component]:
        """List all components."""
        query = self.db.query(Component).filter(Component.project_id == project_id)
        if not include_archived:
            query = query.filter(Component.archived == False)  # noqa: E712
        components = query.all()
        return [schemas.Component.model_validate(component) for component in components]

    def get_component(self, component_id: str, project_id: str) -> schemas.Component:
        """Get a component by ID."""
        component = (
            self.db.query(Component)
            .filter(
                Component.component_id == component_id,
                Component.project_id == project_id,
            )
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")
        workflow = self.workflow_service.get_workflow(component.workflow_id, project_id)
        return schemas.Component.from_orm(component, workflow)

    def create_component(
        self,
        config: schemas.ComponentBase,
        project_id: str | None = None,
    ) -> schemas.Component:
        """Create a new component."""

        # Fill in defaults for non-nullable fields
        requirements = config.requirements or []
        variables = config.variables or []
        spec = config.spec or {"nodes": [], "input_schema": {}}

        # Create workflow for the component
        workflow = self.workflow_service.create_workflow(
            spec=spec,
            requirements=requirements,
            variables=variables,
            ui_metadata=config.ui_metadata or {},
        )

        component = Component(
            name=config.name,
            description=config.description,
            icon=config.icon,
            workflow_id=workflow.workflow_id,
            project_id=project_id,
        )

        self.db.add(component)
        self.db.commit()
        self.db.refresh(component)
        self._log_event(
            VulkanEvent.COMPONENT_CREATED, component_id=component.component_id
        )
        return schemas.Component.from_orm(component, workflow)

    def update_component(
        self,
        component_id: UUID,
        config: schemas.ComponentBase,
        project_id: str | None = None,
    ) -> schemas.Component:
        """Update a component."""
        component = (
            self.db.query(Component)
            .filter(
                Component.component_id == component_id,
                Component.project_id == project_id,
            )
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

        self.db.commit()
        self.db.refresh(component)

        workflow = self.workflow_service.update_workflow(
            workflow_id=component.workflow_id,
            spec=config.spec,
            requirements=config.requirements,
            variables=config.variables,
            ui_metadata=config.ui_metadata,
            project_id=project_id,
        )

        self._log_event(
            VulkanEvent.COMPONENT_UPDATED, component_id=component.component_id
        )
        return schemas.Component.from_orm(component, workflow)

    def delete_component(
        self,
        component_id: UUID,
        project_id: str | None = None,
    ) -> None:
        """Delete (archive) a component."""
        component = (
            self.db.query(Component)
            .filter(
                Component.component_id == component_id,
                Component.project_id == project_id,
            )
            .first()
        )
        if not component:
            raise ComponentNotFoundException(f"Component {component_id} not found")

        # Delete the underlying workflow
        if component.workflow_id:
            self.workflow_service.delete_workflow(component.workflow_id, project_id)

        component.archived = True
        self.db.commit()
        self._log_event(VulkanEvent.COMPONENT_DELETED, component_id=component_id)
