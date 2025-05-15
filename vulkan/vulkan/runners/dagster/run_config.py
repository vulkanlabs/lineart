from dagster import ConfigurableResource


class VulkanRunConfig(ConfigurableResource):
    run_id: str
    server_url: str


RUN_CONFIG_KEY = "vulkan_run_config"


class VulkanPolicyConfig(ConfigurableResource):
    variables: dict
