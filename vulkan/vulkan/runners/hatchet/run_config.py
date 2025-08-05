from dataclasses import dataclass
from typing import Any, Dict, Optional

from pydantic import BaseModel

RUN_CONFIG_KEY = "hatchet_run_config"
POLICY_CONFIG_KEY = "hatchet_policy_config"


@dataclass
class HatchetRunConfig:
    """Configuration for Hatchet run execution."""

    run_id: str
    server_url: str
    hatchet_server_url: str
    hatchet_api_key: Optional[str] = None
    namespace: str = "default"

    @classmethod
    def from_env(cls, run_id: str, server_url: str) -> "HatchetRunConfig":
        """Create configuration from environment variables."""
        import os

        return cls(
            run_id=run_id,
            server_url=server_url,
            hatchet_server_url=os.getenv("HATCHET_SERVER_URL", "http://localhost:8080"),
            hatchet_api_key=os.getenv("HATCHET_API_KEY"),
            namespace=os.getenv("HATCHET_NAMESPACE", "default"),
        )


class HatchetPolicyConfig(BaseModel):
    """Configuration for Hatchet policy execution."""

    variables: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "HatchetPolicyConfig":
        """Create configuration from dictionary."""
        return cls(variables=config)
