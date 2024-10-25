import requests
from dagster import ConfigurableResource, ResourceDependency

from vulkan.dagster.run_config import VulkanRunConfig


class VulkanDataClient(ConfigurableResource):
    run_config: ResourceDependency[VulkanRunConfig]

    def get_data(self, source: str, body: dict, variables: dict) -> requests.Response:
        response = requests.post(
            f"{self.run_config.server_url}/data-broker",
            json={
                "data_source_name": source,
                "request_body": body,
                "variables": variables,
            },
        )
        return response


DATA_CLIENT_KEY = "vulkan_data_client"
