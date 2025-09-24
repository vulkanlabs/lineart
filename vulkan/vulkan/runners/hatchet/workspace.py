import logging
import os

from hatchet_sdk import Hatchet
from hatchet_sdk.config import ClientConfig
from pydantic import BaseModel

from vulkan.runners.hatchet.policy import HatchetFlow
from vulkan.spec.environment.loaders import load_and_resolve_policy

logger = logging.getLogger(__name__)


class HatchetClientConfig(BaseModel):
    token: str
    server_url: str | None = None
    namespace: str | None = None

    @classmethod
    def from_env(cls) -> "HatchetClientConfig":
        """Create configuration from environment variables."""
        token = os.getenv("HATCHET_CLIENT_TOKEN")
        if not token:
            raise ValueError("HATCHET_CLIENT_TOKEN is not set")

        server_url = os.getenv("HATCHET_SERVER_URL", None)
        namespace = os.getenv("HATCHET_NAMESPACE", "default")

        return cls(
            server_url=server_url,
            token=token,
            namespace=namespace,
        )


class HatchetWorkspaceManager:
    """Manages Hatchet workspace, workers, and workflow execution."""

    def __init__(
        self,
        hatchet_client_config: HatchetClientConfig,
        spec_file_path: str,
        workflow_id: str,
    ):
        if not os.path.exists(spec_file_path):
            raise ValueError(f"Spec file does not exist: {spec_file_path}")

        self.workflow_id = workflow_id
        self.config = hatchet_client_config
        server_url = (
            self.config.server_url
            if self.config.server_url
            else ClientConfig().server_url
        )
        self.client = Hatchet(
            config=ClientConfig(
                server_url=server_url,
                token=self.config.token,
                namespace=self.config.namespace,
            ),
        )

        policy = load_and_resolve_policy(spec_file_path)
        hatchet_flow = HatchetFlow(policy.nodes, policy_name=self.workflow_id)
        self._hatchet_workflow = hatchet_flow.create_workflow()
        # For now, we're creating one worker per workflow/workspace.
        self._worker = self.client.worker(
            f"vulkan-worker-{self.workflow_id}",
            workflows=[self._hatchet_workflow],
        )

        logger.info(
            f"Initialized Hatchet workspace for namespace: {self.config.namespace}"
        )

    def start_worker(self) -> None:
        """Start the Hatchet worker."""
        try:
            logger.info("Starting Hatchet worker...")
            self._worker.start()
        except Exception as e:
            logger.error(f"Failed to start worker: {e}")
            raise

    def stop_worker(self) -> None:
        """Stop the Hatchet worker."""
        try:
            self._worker.stop()
            logger.info("Stopped Hatchet worker")
        except Exception as e:
            logger.error(f"Failed to stop worker: {e}")

    def cleanup(self) -> None:
        """Clean up resources."""
        self.stop_worker()
        self.client = None
        self._worker = None


HATCHET_ENTRYPOINT = """
from vulkan.runners.hatchet.workspace import HatchetWorkspaceManager, HatchetClientConfig

if __name__ == "__main__":
    hatchet_client_config = HatchetClientConfig.from_env()
    manager = HatchetWorkspaceManager(
        hatchet_client_config=hatchet_client_config,
        spec_file_path="{spec_file_path}",
        workflow_id="{workflow_id}",
    )

    manager.start_worker()
"""
