import os

from pydantic.dataclasses import dataclass


@dataclass
class VulkanConfig:
    home: str
    server_path: str
    scripts_path: str
    workspaces_path: str


def get_vulkan_config() -> VulkanConfig:
    VULKAN_HOME = os.getenv("VULKAN_HOME")
    VULKAN_SCRIPTS_PATH = os.getenv("VULKAN_SCRIPTS_PATH")
    VULKAN_SERVER_PATH = os.getenv("VULKAN_SERVER_PATH")

    if not VULKAN_HOME or not VULKAN_SERVER_PATH:
        raise ValueError("Vulkan configuration missing")

    return VulkanConfig(
        home=VULKAN_HOME,
        server_path=VULKAN_SERVER_PATH,
        scripts_path=VULKAN_SCRIPTS_PATH,
        workspaces_path=f"{VULKAN_HOME}/workspaces",
    )
