from enum import Enum

from dagster import ConfigurableResource


class RunStatus(Enum):
    PENDING = "PENDING"
    STARTED = "STARTED"
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


class VulkanRunConfig(ConfigurableResource):
    policy_id: int
    run_id: int
    server_url: str


RUN_CONFIG_KEY = "vulkan_run_config"
