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


class VulkanRunClient(ConfigurableResource):
    run_config: ResourceDependency[VulkanRunConfig]

    def run_version_sync(
        self,
        policy_version_id: str,
        data: dict,
        time_step_ms: int,
        timeout_ms: int,
    ) -> dict:
        response = requests.post(
            f"{self.run_config.server_url}/policy-versions/{policy_version_id}/runs/",
            json=data,
        )
        if response.status_code != 200:
            raise ValueError(
                f"Failed to create run for policy version {policy_version_id}: {response.text}"
            )
        run_id = response.json().get("run_id")
        # TODO: get results too
        success, data = self._poll_run_status(
            run_id,
            time_step_ms=time_step_ms,
            timeout_ms=timeout_ms,
        )

        return {
            "run_id": run_id,
            "success": success,
            "data": data,
        }

    def _poll_run_status(
        self,
        run_id: str,
        time_step_ms: int,
        timeout_ms: int,
    ) -> tuple[bool, dict]:
        url = f"{self.run_config.server_url}/runs/{run_id}"

        for _ in range(0, timeout_ms, time_step_ms):
            response = requests.get(url)
            try:
                data = response.json()
            except (KeyError, json.decoder.JSONDecodeError):
                time.sleep(time_step_ms / 1000)
                continue
            status = data["status"]
            return status == "SUCCESS", data

        return False, {}
