import logging
from typing import Any, Dict, List, Optional

from hatchet_sdk import Context, Hatchet
from hatchet_sdk.worker import Worker

from vulkan.runners.hatchet.resources import create_hatchet_resources
from vulkan.runners.hatchet.run_config import HatchetPolicyConfig, HatchetRunConfig

logger = logging.getLogger(__name__)


class HatchetWorkspaceManager:
    """Manages Hatchet workspace, workers, and workflow execution."""

    def __init__(self, config: HatchetRunConfig):
        self.config = config
        self.client: Optional[Hatchet] = None
        self.worker: Optional[Worker] = None
        self.resources = create_hatchet_resources(config)

    def initialize(self) -> None:
        """Initialize Hatchet client and worker."""
        try:
            self.client = Hatchet(
                server_url=self.config.hatchet_server_url,
                token=self.config.hatchet_api_key,
                namespace=self.config.namespace,
            )

            self.worker = self.client.worker("vulkan-worker")
            logger.info(
                f"Initialized Hatchet workspace for namespace: {self.config.namespace}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Hatchet workspace: {e}")
            raise

    def register_workflow(self, workflow_name: str, workflow_fn: Any) -> None:
        """Register a workflow with the worker."""
        if not self.worker:
            raise RuntimeError("Worker not initialized. Call initialize() first.")

        try:
            self.worker.register_workflow(workflow_fn)
            logger.info(f"Registered workflow: {workflow_name}")
        except Exception as e:
            logger.error(f"Failed to register workflow {workflow_name}: {e}")
            raise

    def start_worker(self) -> None:
        """Start the Hatchet worker."""
        if not self.worker:
            raise RuntimeError("Worker not initialized. Call initialize() first.")

        try:
            logger.info("Starting Hatchet worker...")
            self.worker.start()
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            raise

    def stop_worker(self) -> None:
        """Stop the Hatchet worker."""
        if self.worker:
            try:
                self.worker.stop()
                logger.info("Stopped Hatchet worker")
            except Exception as e:
                logger.error(f"Failed to stop worker: {e}")

    def trigger_workflow(self, workflow_name: str, input_data: Dict[str, Any]) -> str:
        """Trigger a workflow execution."""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        try:
            workflow_run = self.client.admin.run_workflow(
                workflow_name=workflow_name, input=input_data
            )
            logger.info(
                f"Triggered workflow {workflow_name} with run ID: {workflow_run.workflow_run_id}"
            )
            return workflow_run.workflow_run_id
        except Exception as e:
            logger.error(f"Failed to trigger workflow {workflow_name}: {e}")
            raise

    def get_workflow_status(self, workflow_run_id: str) -> Dict[str, Any]:
        """Get the status of a workflow run."""
        if not self.client:
            raise RuntimeError("Client not initialized. Call initialize() first.")

        try:
            # Note: This would need to be implemented based on Hatchet SDK capabilities
            # For now, return a placeholder
            return {
                "workflow_run_id": workflow_run_id,
                "status": "RUNNING",  # This would be fetched from Hatchet
            }
        except Exception as e:
            logger.error(f"Failed to get workflow status for {workflow_run_id}: {e}")
            raise

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_worker()
        self.client = None
        self.worker = None
