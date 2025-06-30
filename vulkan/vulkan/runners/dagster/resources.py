import json
import time

import requests
from dagster import ConfigurableResource, ResourceDependency

from vulkan.runners.dagster.run_config import VulkanRunConfig

DATA_CLIENT_KEY = "vulkan_data_client"
RUN_CLIENT_KEY = "vulkan_run_client"


class VulkanDataClient(ConfigurableResource):
    run_config: ResourceDependency[VulkanRunConfig]

    def get_data(
        self, data_source: str, configured_params: dict, run_id: str
    ) -> requests.Response:
        response = requests.post(
            f"{self.run_config.server_url}/data-broker",
            json={
                "data_source_name": data_source,
                "configured_params": configured_params,
                "run_id": run_id,
            },
        )
        return response


class VulkanRunClient(ConfigurableResource):
    run_config: ResourceDependency[VulkanRunConfig]

    def run_version_sync(
        self,
        policy_version_id: str,
        data: dict,
    ) -> dict:
        response = requests.post(
            f"{self.run_config.server_url}/policy-versions/{policy_version_id}/run/",
            json=data,
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to create run for policy version {policy_version_id}: {response.text}"
            )
        run_result = response.json()

        return {
            "run_id": run_result["run_id"],
            "status": run_result["status"],
            "result": run_result["result"],
            "data": run_result["run_metadata"],
        }
