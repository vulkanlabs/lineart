"""Dagster backend implementation for workflow execution."""

from dagster_graphql import DagsterGraphQLClient
from vulkan.runners.dagster.policy import DEFAULT_POLICY_NAME
from vulkan.runners.shared.constants import POLICY_CONFIG_KEY, RUN_CONFIG_KEY

from vulkan_engine.backends.dagster import trigger_run
from vulkan_engine.backends.execution import ExecutionBackend
from vulkan_engine.logging import get_logger

logger = get_logger(__name__)


class DagsterBackend(ExecutionBackend):
    """Dagster implementation of the execution backend."""

    def __init__(self, dagster_client: DagsterGraphQLClient, app_server_url: str):
        """
        Initialize Dagster backend.

        Args:
            dagster_client: Dagster GraphQL client
            server_url: Server URL for callbacks
        """
        self.dagster_client = dagster_client
        self.server_url = app_server_url

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
        Trigger a Dagster job execution.

        Args:
            workflow_id: ID of the workflow to execute
            run_id: UUID of the run
            input_data: Input data for the workflow
            input_schema: Schema for the input data
            config_variables: Configuration variables for the workflow
            project_id: Optional project UUID

        Returns:
            Dagster run ID

        Raises:
            Exception: If Dagster job triggering fails
        """
        execution_config = {
            "ops": {"input_node": {"config": input_data}},
            "resources": {
                RUN_CONFIG_KEY: {
                    "config": {
                        "run_id": str(run_id),
                        "project_id": str(project_id) if project_id else None,
                        "server_url": self.server_url,
                    }
                },
                POLICY_CONFIG_KEY: {"config": {"variables": config_variables}},
            },
        }
        logger.debug(f"Triggering job with config: {execution_config}")

        backend_run_id = trigger_run.trigger_dagster_job(
            self.dagster_client,
            workflow_id,
            DEFAULT_POLICY_NAME,
            execution_config,
        )
        return backend_run_id
