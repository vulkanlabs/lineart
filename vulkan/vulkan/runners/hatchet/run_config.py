from dataclasses import dataclass
from typing import Any, Dict

from pydantic import BaseModel

RUN_CONFIG_KEY = "hatchet_run_config"
POLICY_CONFIG_KEY = "hatchet_policy_config"


@dataclass
class HatchetRunConfig:
    """Configuration for Hatchet run execution."""

    run_id: str
    server_url: str


class HatchetPolicyConfig(BaseModel):
    """Configuration for Hatchet policy execution."""

    variables: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "HatchetPolicyConfig":
        """Create configuration from dictionary."""
        return cls(variables=config)
