from dagster import ConfigurableResource, ResourceDependency

from vulkan.runners.dagster.run_config import (
    DagsterVulkanPolicyConfig,
    DagsterVulkanRunConfig,
)
from vulkan.runners.shared.app_client import BaseAppClient, create_app_client
from vulkan.runners.shared.run_config import VulkanRunConfig as SharedRunConfig


class AppClientResource(ConfigurableResource):
    """
    Unified client resource for app server communication with optional JWT authentication.

    The client is created once per run and reuses the same JWT token (if enabled)
    for all requests within that run.
    """

    run_config: ResourceDependency[DagsterVulkanRunConfig]
    _client: BaseAppClient | None = None

    def get_client(self) -> BaseAppClient:
        """
        Get or create the app client (singleton per run).

        Returns:
            BaseAppClient: Either SimpleAppClient or JWTAppClient based on configuration
        """
        if self._client is None:
            shared: SharedRunConfig = self.run_config.to_shared()
            self._client = create_app_client(
                run_id=shared.run_id,
                project_id=shared.project_id,
                server_url=shared.server_url,
                data_broker_url=shared.data_broker_url,
            )
        return self._client
