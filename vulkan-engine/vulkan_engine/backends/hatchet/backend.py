"""Dagster backend implementation for workflow execution."""

from dataclasses import asdict

from hatchet_sdk import ClientConfig, Hatchet, TriggerWorkflowOptions
from pydantic import ValidationError, create_model
from vulkan.runners.shared.constants import POLICY_CONFIG_KEY, RUN_CONFIG_KEY
from vulkan.runners.shared.run_config import VulkanPolicyConfig, VulkanRunConfig

from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.config import AppConfig, WorkerServiceConfig
from vulkan_engine.logging import get_logger

logger = get_logger(__name__)


class HatchetBackend(ExecutionBackend):
    """Dagster implementation of the execution backend."""

    def __init__(
        self,
        worker_config: WorkerServiceConfig,
        server_config: AppConfig,
    ) -> None:
        """
        Initialize Hatchet backend.

        Args:
            worker_config: WorkerServiceConfig
            server_config: AppConfig, configuration related to Vulkan App server.

        """
        self._worker_config = worker_config
        self._server_config = server_config
        client_cfg = ClientConfig(token=worker_config.service_config.hatchet_token)
        self.client = Hatchet(config=client_cfg)

    def trigger_job(
        self,
        run_id: str,
        workflow_id: str,
        input_data: dict,
        input_schema: dict,
        config_variables: dict[str, str],
        project_id: str | None = None,
    ) -> str:
        """
        Trigger a job execution.

        Args:
            workflow_id: ID of the workflow to execute
            run_id: UUID of the run
            input_data: Input data for the workflow
            input_schema: Input schema for the workflow
            config_variables: Configuration variables for the workflow
            project_id: Optional project UUID

        Returns:
            Dagster run ID

        Raises:
            Exception: If Dagster job triggering fails
        """

        input_type = create_model("inputType", **input_schema)
        stub_workflow = self.client.workflow(
            name=workflow_id,
            input_validator=input_type,
        )

        run_cfg = VulkanRunConfig(
            run_id=str(run_id),
            server_url=self._server_config.server_url,
            project_id=str(project_id) if project_id else None,
        )
        policy_cfg = VulkanPolicyConfig(variables=config_variables)

        metadata = {
            RUN_CONFIG_KEY: asdict(run_cfg),
            POLICY_CONFIG_KEY: asdict(policy_cfg),
        }
        options = TriggerWorkflowOptions(
            additional_metadata=metadata,
        )

        try:
            run_inputs = input_type.model_validate(input_data)
        except ValidationError as e:
            raise ValueError(f"[workflow {workflow_id}] Invalid input data") from e

        try:
            run_ref = stub_workflow.run_no_wait(run_inputs, options=options)
        except Exception as e:
            logger.error(f"Failed to trigger workflow {workflow_id}: {e}")
            raise RuntimeError(f"[workflow {workflow_id}] Failed to trigger") from e
        return run_ref.workflow_run_id
