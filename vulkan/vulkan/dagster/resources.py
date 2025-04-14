import requests
from dagster import ConfigurableResource, ResourceDependency

from vulkan.dagster.run_config import VulkanRunConfig


class VulkanDataClient(ConfigurableResource):
    run_config: ResourceDependency[VulkanRunConfig]

    def get_data(
        self, data_source: str, body: dict, variables: dict, run_id: str
    ) -> requests.Response:
        response = requests.post(
            f"{self.run_config.server_url}/data-broker",
            json={
                "data_source_name": data_source,
                "request_body": body,
                "variables": variables,
                "run_id": run_id,
            },
        )
        return response


DATA_CLIENT_KEY = "vulkan_data_client"
