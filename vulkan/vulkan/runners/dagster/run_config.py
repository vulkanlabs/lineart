from dagster import ConfigurableResource


class VulkanRunConfig(ConfigurableResource):
    run_id: str
    server_url: str
    project_id: str | None = None


class VulkanPolicyConfig(ConfigurableResource):
    variables: dict
