from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass
class VulkanRunConfig:
    """Configuration for Hatchet run execution."""

    run_id: str
    server_url: str
    project_id: str | None = None


@dataclass
class VulkanPolicyConfig:
    """Configuration for Hatchet policy execution."""

    variables: Dict[str, Any] = field(default_factory=dict)
