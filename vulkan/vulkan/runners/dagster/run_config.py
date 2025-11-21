import os

from dagster import ConfigurableResource
from pydantic import Field

from vulkan.runners.shared.run_config import VulkanPolicyConfig, VulkanRunConfig


class DagsterVulkanRunConfig(ConfigurableResource):
    """Dagster wrapper that produces the shared VulkanRunConfig dataclass."""

    run_id: str
    server_url: str
    project_id: str | None = None
    data_broker_url: str | None = Field(
        default_factory=lambda: os.getenv("DATA_BROKER_URL")
    )

    def to_shared(self) -> VulkanRunConfig:
        return VulkanRunConfig(
            run_id=self.run_id,
            server_url=self.server_url,
            project_id=self.project_id,
            data_broker_url=self.data_broker_url,
        )


class DagsterVulkanPolicyConfig(ConfigurableResource):
    """Dagster wrapper that produces the shared VulkanPolicyConfig dataclass."""

    variables: dict

    def to_shared(self) -> VulkanPolicyConfig:
        return VulkanPolicyConfig(variables=self.variables)
