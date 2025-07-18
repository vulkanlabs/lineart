"""
Workflow service.

Handles internal workflow operations. Workflows should never be exposed directly
to API users but are managed internally by PolicyVersionService and ComponentService.
"""

from typing import Any

from sqlalchemy.orm import Session

from vulkan.core.run import WorkflowStatus
from vulkan.spec.policy import PolicyDefinitionDict
from vulkan_engine.dagster.service_client import VulkanDagsterServiceClient
from vulkan_engine.db import Workflow
from vulkan_engine.events import VulkanEvent
from vulkan_engine.exceptions import WorkflowNotFoundException
from vulkan_engine.logger import VulkanLogger
from vulkan_engine.schemas import UIMetadata
from vulkan_engine.services.base import BaseService

class WorkflowService(BaseService):
    """Service for internal workflow operations."""

    def __init__(
        self,
        db: Session,
        dagster_service_client: VulkanDagsterServiceClient | None = None,
        logger: VulkanLogger | None = None,
    ):
        super().__init__(db, logger)
        self.dagster_service_client = dagster_service_client

    def create_workflow(
        self,
        spec: PolicyDefinitionDict | None = None,
        requirements: list[str] | None = None,
        variables: list[str] | None = None,
        ui_metadata: dict[str, UIMetadata] | None = None,
        project_id: str | None = None,
    ) -> Workflow:
        """
        Create a new workflow.

        Args:
            spec: Workflow specification
            input_schema: Input schema for the workflow
            requirements: List of requirements
            variables: List of variables
            ui_metadata: UI metadata

        Returns:
            Created Workflow object
        """
        workflow = Workflow(
            spec=spec,
            requirements=requirements,
            variables=variables,
            status=WorkflowStatus.INVALID,
            ui_metadata=ui_metadata,
            project_id=project_id,
        )
        self.db.add(workflow)
        self.db.commit()
        self.db.refresh(workflow)

        self._log_event(VulkanEvent.WORKFLOW_CREATED, workflow_id=workflow.workflow_id)
        return workflow

    def get_workflow(self, workflow_id: str, project_id: str | None = None) -> Workflow:
        """
        Get a workflow by ID.

        Args:
            workflow_id: Workflow UUID

        Returns:
            Workflow object

        Raises:
            WorkflowNotFoundException: If workflow doesn't exist
        """

        workflow = (
            self.db.query(Workflow)
            .filter(
                Workflow.workflow_id == workflow_id, Workflow.project_id == project_id
            )
            .first()
        )
        if not workflow:
            raise WorkflowNotFoundException(f"Workflow {workflow_id} not found")
        return workflow

    def update_workflow(
        self,
        workflow_id: str,
        spec: PolicyDefinitionDict | None = None,
        requirements: list[str] | None = None,
        variables: list[str] | None = None,
        ui_metadata: dict[str, UIMetadata] | None = None,
        project_id: str | None = None,
    ) -> Workflow:
        """
        Update a workflow.

        Args:
            workflow_id: Workflow UUID
            spec: New workflow specification
            input_schema: New input schema
            requirements: New requirements list
            variables: New variables list
            ui_metadata: New UI metadata

        Returns:
            Updated Workflow object

        Raises:
            WorkflowNotFoundException: If workflow doesn't exist
        """

        workflow = self.get_workflow(workflow_id, project_id)

        # Update the underlying workflow
        spec = self._convert_pydantic_to_dict(spec)
        if spec is not None:
            workflow.spec = spec
        if requirements is not None:
            workflow.requirements = requirements
        if variables is not None:
            workflow.variables = variables
        if ui_metadata is not None:
            workflow.ui_metadata = self._convert_pydantic_to_dict(ui_metadata)

        workflow.status = WorkflowStatus.INVALID
        self.db.commit()
        self.db.refresh(workflow)

        # Ensure the workspace is created or updated with the new spec and requirements
        self._update_dagster_workspace(workflow)
        workflow.status = WorkflowStatus.VALID
        self.db.commit()
        self.db.refresh(workflow)

        self._log_event(VulkanEvent.WORKFLOW_UPDATED, workflow_id=workflow.workflow_id)
        return workflow

    def delete_workflow(self, workflow_id: str, project_id: str | None = None) -> None:
        """
        Delete a workflow.

        Args:
            workflow_id: Workflow UUID

        Raises:
            WorkflowNotFoundException: If workflow doesn't exist
        """

        workflow = self.get_workflow(workflow_id, project_id)
        self.db.delete(workflow)
        self.db.commit()

        # Remove from Dagster
        name = str(workflow_id)
        try:
            self.dagster_service_client.delete_workspace(name)
            self.dagster_service_client.ensure_workspace_removed(name)
        except Exception as e:
            raise Exception(f"Error deleting workflow {workflow_id}: {str(e)}")

        self._log_event(VulkanEvent.WORKFLOW_DELETED, workflow_id=workflow_id)

    def _update_dagster_workspace(
        self,
        workflow: Workflow,
    ) -> None:
        """Update Dagster workspace for the policy version."""
        try:
            self.dagster_service_client.update_workspace(
                workspace_id=workflow.workflow_id,
                spec=workflow.spec,
                requirements=workflow.requirements,
            )
        except ValueError as e:
            if self.logger:
                self.logger.system.error(
                    f"Failed to update workspace ({workflow.workflow_id}): {e}",
                    exc_info=True,
                )
            raise Exception(
                f"Failed to update workspace. Workflow ID: {workflow.workflow_id}"
            )

        try:
            self.dagster_service_client.ensure_workspace_added(
                str(workflow.workflow_id)
            )
            workflow.status = WorkflowStatus.VALID
        except ValueError as e:
            if self.logger:
                self.logger.system.error(
                    f"Failed to update workspace ({workflow.workflow_id}), version is invalid:\n{e}",
                    exc_info=False,
                )
