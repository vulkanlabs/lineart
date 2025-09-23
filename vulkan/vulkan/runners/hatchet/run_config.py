from dataclasses import dataclass, field
from typing import Any, Dict

RUN_CONFIG_KEY = "vulkan_run_config"
POLICY_CONFIG_KEY = "vulkan_policy_config"


@dataclass
class HatchetRunConfig:
    """Configuration for Hatchet run execution."""

    run_id: str
    server_url: str
    hatchet_api_key: str
    project_id: str | None = None


@dataclass
class HatchetPolicyConfig:
    """Configuration for Hatchet policy execution."""

    variables: Dict[str, Any] = field(default_factory=dict)
