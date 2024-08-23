import os
from dataclasses import dataclass


def version_name(policy_id: int, policy_version_id: int) -> str:
    return f"policy-{policy_id}-version-{policy_version_id}"


@dataclass
class VulkanServerConfig:
    server_url: str
    vulkan_dagster_server_url: str

    metrics_max_days: int = 30


def get_vulkan_server_config() -> VulkanServerConfig:
    app_port = os.getenv("APP_PORT")
    vulkan_dagster_server_url = os.getenv("VULKAN_DAGSTER_SERVER_URL")
    return VulkanServerConfig(
        server_url=f"http://app:{app_port}",
        vulkan_dagster_server_url=vulkan_dagster_server_url,
    )
