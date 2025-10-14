from dagster import ConfigurableResource, ResourceDependency

from vulkan.runners.shared.app_client import BaseAppClient, create_app_client


class VulkanRunConfig(ConfigurableResource):
    run_id: str
    server_url: str
    project_id: str | None = None


class VulkanPolicyConfig(ConfigurableResource):
    variables: dict


class AppClientResource(ConfigurableResource):
    """
    Unified client resource for app server communication with optional JWT authentication.

    The client is created once per run and reuses the same JWT token (if enabled)
    for all requests within that run.
    """

    run_config: ResourceDependency[VulkanRunConfig]
    _client: BaseAppClient | None = None

    def get_client(self) -> BaseAppClient:
        """
        Get or create the app client (singleton per run).

        Returns:
            BaseAppClient: Either SimpleAppClient or JWTAppClient based on configuration
        """
        if self._client is None:
            self._client = create_app_client(
                run_id=self.run_config.run_id,
                project_id=self.run_config.project_id,
                server_url=self.run_config.server_url,
            )
        return self._client
