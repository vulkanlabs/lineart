import os
from dataclasses import dataclass


def version_name(policy_id: int, policy_version_id: int) -> str:
    return f"policy-{policy_id}-version-{policy_version_id}"


@dataclass
class VulkanServerConfig:
    server_url: str
    vulkan_dagster_server_url: str
    upload_service_url: str

    metrics_max_days: int = 30


def get_vulkan_server_config() -> VulkanServerConfig:
    app_host = os.getenv("APP_HOST")
    app_port = os.getenv("APP_PORT")
    if app_host is None or app_port is None:
        raise ValueError("APP_HOST and APP_PORT must be set")

    dagster_host = os.getenv("DAGSTER_HOST")
    dagster_server_port = os.getenv("DAGSTER_SERVER_PORT")
    if dagster_host is None or dagster_server_port is None:
        raise ValueError("DAGSTER_HOST and DAGSTER_SERVER_PORT must be set")

    upload_service_host = os.getenv("UPLOAD_SERVICE_HOST")
    upload_service_port = os.getenv("UPLOAD_SERVICE_PORT")
    if upload_service_host is None or upload_service_port is None:
        raise ValueError("UPLOAD_SERVICE_HOST and UPLOAD_SERVICE_PORT must be set")

    return VulkanServerConfig(
        server_url=f"http://{app_host}:{app_port}",
        vulkan_dagster_server_url=f"http://{dagster_host}:{dagster_server_port}",
        upload_service_url=f"http://{upload_service_host}:{upload_service_port}",
    )
