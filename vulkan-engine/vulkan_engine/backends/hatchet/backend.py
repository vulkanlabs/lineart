"""Dagster backend implementation for workflow execution."""

from dataclasses import asdict

from hatchet_sdk import ClientConfig, Hatchet, TriggerWorkflowOptions
from pydantic import ValidationError, create_model

from vulkan.constants import POLICY_CONFIG_KEY
from vulkan.runners.dagster.run_config import RUN_CONFIG_KEY
from vulkan.runners.hatchet.run_config import HatchetPolicyConfig, HatchetRunConfig
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.config import WorkerServiceConfig
from vulkan_engine.logger import init_logger

logger = init_logger("hatchet_backend")


class HatchetBackend(ExecutionBackend):
    """Dagster implementation of the execution backend."""

    def __init__(self, config: WorkerServiceConfig):
        """
        Initialize Hatchet backend.

        Args:
            server_url: Server URL for callbacks
        """
        self._config = config
        client_cfg = ClientConfig(token=config.service_config.hatchet_token)
        self.client = Hatchet(config=client_cfg)
        self.server_url = config.server_url

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
            name=workflow_id, input_validator=input_type
        )

        server_url = None  # TODO: Needs to be passed in from the backend config
        run_cfg = HatchetRunConfig(
            run_id=run_id,
            server_url=server_url,
            project_id=str(project_id) if project_id else None,
            hatchet_api_key=self._config.service_config.hatchet_token,
        )
        policy_cfg = HatchetPolicyConfig(variables=config_variables)

        metadata = {
            RUN_CONFIG_KEY: asdict(run_cfg),
            POLICY_CONFIG_KEY: asdict(policy_cfg),
        }
        options = TriggerWorkflowOptions(additional_metadata=metadata)
        logger.debug(f"Triggering job with config: {metadata}")

        try:
            run_inputs = input_type.model_validate(input_data)
        except ValidationError as e:
            raise ValueError(f"[workflow {workflow_id}] Invalid input data") from e

        logger.debug(f"Triggering job with inputs: {run_inputs}")
        run_ref = stub_workflow.run_no_wait(run_inputs, options=options)
        logger.debug(f"Triggered job with run ID: {run_ref.workflow_run_id}")
        return run_ref.workflow_run_id
