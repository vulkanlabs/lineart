"""
Workflow service.

Handles internal workflow operations. Workflows should never be exposed directly
to API users but are managed internally by PolicyVersionService and ComponentService.
"""

from sqlalchemy.orm import Session
from vulkan.core.run import WorkflowStatus
from vulkan.spec.nodes import NodeType
from vulkan.spec.policy import PolicyDefinitionDict

from vulkan_engine.backends.service_client import BackendServiceClient
from vulkan_engine.db import Workflow
from vulkan_engine.exceptions import WorkflowNotFoundException
from vulkan_engine.loaders.component import ComponentLoader
from vulkan_engine.logging import get_logger
from vulkan_engine.schemas import UIMetadata
from vulkan_engine.services.base import BaseService


class WorkflowService(BaseService):
    """Service for internal workflow operations."""

    def __init__(
        self,
        db: Session,
        backend_service_client: BackendServiceClient | None = None,
    ):
        super().__init__(db)
        self.worker_service_client = backend_service_client
        self.component_loader = ComponentLoader(db)
        self.logger = get_logger(__name__)

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
        spec, requirements = self._inject_component_implementations(
            spec,
            requirements,
            project_id,
        )
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
        self._update_worker_workspace(workflow)
        workflow.status = WorkflowStatus.VALID
        self.db.commit()
        self.db.refresh(workflow)

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

        # Remove from worker service
        name = str(workflow_id)
        try:
            if self.worker_service_client:
                self.worker_service_client.delete_workspace(name)
                self.worker_service_client.ensure_workspace_removed(name)
        except Exception as e:
            raise Exception(f"Error deleting workflow {workflow_id}: {str(e)}")

    def _update_worker_workspace(
        self,
        workflow: Workflow,
    ) -> None:
        """Update worker service workspace for the policy version."""
        try:
            if self.worker_service_client:
                self.worker_service_client.update_workspace(
                    workspace_id=workflow.workflow_id,
                    spec=workflow.spec,
                    requirements=workflow.requirements,
                )
        except ValueError as e:
            self.logger.error(
                "failed_to_update_workspace",
                workflow_id=workflow.workflow_id,
                error=str(e),
                exc_info=True,
            )
            raise Exception(
                f"Failed to update workspace. Workflow ID: {workflow.workflow_id}"
            )

        try:
            if self.worker_service_client:
                self.worker_service_client.ensure_workspace_added(
                    str(workflow.workflow_id)
                )
            workflow.status = WorkflowStatus.VALID
        except ValueError as e:
            self.logger.error(
                "workspace_invalid",
                workflow_id=workflow.workflow_id,
                error=str(e),
            )

    def _inject_component_implementations(
        self,
        spec: PolicyDefinitionDict,
        requirements: list[str] | None,
        project_id: str | None = None,
    ) -> tuple[PolicyDefinitionDict, list[str]]:
        """Inject component implementations into the spec.

        Component implementations are injected into the spec for each component node.
        This is done on saving the workflow.
        """
        if spec is None or spec.get("nodes") is None:
            return spec, requirements

        if requirements is None:
            requirements = []

        component_requirements = []
        definition = PolicyDefinitionDict.model_validate(spec)
        new_nodes = []
        for node in definition.nodes:
            if node.node_type == NodeType.COMPONENT.value:
                component_name = node.metadata.get("component_name")
                if component_name is None:
                    raise ValueError(f"Component node {node.name} has no component ID")

                component = self.component_loader.get_component(
                    name=component_name,
                    project_id=project_id,
                    include_archived=False,
                )
                node.metadata["definition"] = self._convert_pydantic_to_dict(
                    component.workflow.spec
                )
                component_requirements.extend(component.workflow.requirements)
            new_nodes.append(node)

        definition.nodes = new_nodes
        new_spec = self._convert_pydantic_to_dict(definition)

        # TODO: This would probably be better with a dedicated requirement
        # type that can be used to differentiate between component requirements
        # and workflow requirements.
        if len(component_requirements) > 0:
            requirements = list(set(requirements + component_requirements))

        return new_spec, requirements
