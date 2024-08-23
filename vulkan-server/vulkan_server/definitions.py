from dataclasses import dataclass

from dotenv import dotenv_values


def version_name(policy_id: int, policy_version_id: int) -> str:
    return f"policy-{policy_id}-version-{policy_version_id}"


@dataclass
class VulkanServerConfig:
    server_url: str
    vulkan_dagster_server_url: str

    metrics_max_days: int = 30


def get_vulkan_server_config() -> VulkanServerConfig:
    config = dotenv_values()
    return VulkanServerConfig(
        server_url=f"http://app:{config['APP_PORT']}",
        vulkan_dagster_server_url=config["VULKAN_DAGSTER_SERVER_URL"],
    )
