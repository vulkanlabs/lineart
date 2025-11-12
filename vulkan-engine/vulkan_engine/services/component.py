"""
Component service.

Handles business logic for component operations.
"""

from typing import List

from sqlalchemy.orm import Session

from vulkan_engine import schemas
from vulkan_engine.db import Component
from vulkan_engine.exceptions import (
    WorkflowNotFoundException,
)
from vulkan_engine.loaders.component import ComponentLoader
from vulkan_engine.services.base import BaseService
from vulkan_engine.services.workflow import WorkflowService


class ComponentService(BaseService):
    """Service for component operations."""

    def __init__(
        self,
        db: Session,
        workflow_service: WorkflowService,
    ):
        super().__init__(db)
        self.workflow_service = workflow_service
        self.component_loader = ComponentLoader(db)

    def list_components(
        self,
        include_archived: bool = False,
        project_id: str | None = None,
    ) -> List[schemas.Component]:
        """List all components."""
        components = self.component_loader.list_components(
            project_id=project_id,
            include_archived=include_archived,
        )
        return components

    def get_component(self, component_name: str, project_id: str = None) -> Component:
        """Get a component by name."""
        component = self.component_loader.get_component(
            name=component_name,
            project_id=project_id,
        )
        return component

    def create_component(
        self,
        config: schemas.ComponentBase,
        project_id: str | None = None,
    ) -> schemas.Component:
        """Create a new component."""

        # Create workflow for the component
        workflow = self.workflow_service.create_workflow(
            spec={"nodes": [], "input_schema": {}},
            requirements=[],
            variables=[],
            ui_metadata={},
            project_id=project_id,
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
        return schemas.Component.from_orm(component, workflow)

    def update_component(
        self,
        component_name: str,
        config: schemas.ComponentUpdate,
        project_id: str | None = None,
    ) -> schemas.Component:
        """Update a component."""
        component = self.get_component(
            component_name=component_name,
            project_id=project_id,
        )

        # Update component fields
        if config.name is not None:
            component.name = config.name
        if config.description is not None:
            component.description = config.description
        if config.icon is not None:
            component.icon = config.icon

        self.db.commit()
        self.db.refresh(component)

        workflow = component.workflow

        # Update the underlying workflow if provided
        if config.workflow is not None:
            workflow = self.workflow_service.update_workflow(
                workflow_id=component.workflow_id,
                spec=config.workflow.spec,
                requirements=config.workflow.requirements,
                variables=config.workflow.variables,
                ui_metadata=config.workflow.ui_metadata,
                project_id=project_id,
            )

        return schemas.Component.from_orm(component, workflow)

    def delete_component(
        self,
        component_name: str,
        project_id: str | None = None,
    ) -> None:
        """Delete (archive) a component."""
        component = self.get_component(
            component_name=component_name,
            project_id=project_id,
        )

        # Delete the underlying workflow
        if component.workflow_id:
            try:
                self.workflow_service.delete_workflow(component.workflow_id, project_id)
            except WorkflowNotFoundException:
                pass

        component.archived = True
        self.db.commit()
