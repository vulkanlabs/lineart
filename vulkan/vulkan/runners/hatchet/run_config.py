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
    hatchet_server_url: str
    hatchet_api_key: str
    namespace: str = "default"

    @classmethod
    def from_env(cls, run_id: str, server_url: str) -> "HatchetRunConfig":
        """Create configuration from environment variables."""
        import os

        hatchet_api_key = os.getenv("HATCHET_CLIENT_TOKEN")
        if not hatchet_api_key:
            raise ValueError("HATCHET_CLIENT_TOKEN environment variable is required")

        # The Hatchet SDK can extract server URL from the token,
        # but we'll set a default in case it's provided explicitly
        hatchet_server_url = os.getenv("HATCHET_SERVER_URL", "")
        namespace = os.getenv("HATCHET_NAMESPACE", "default")

        return cls(
            run_id=run_id,
            server_url=server_url,
            hatchet_server_url=hatchet_server_url,
            hatchet_api_key=hatchet_api_key,
            namespace=namespace,
        )


class HatchetPolicyConfig(BaseModel):
    """Configuration for Hatchet policy execution."""

    variables: Dict[str, Any] = {}

    @classmethod
    def from_dict(cls, config: Dict[str, Any]) -> "HatchetPolicyConfig":
        """Create configuration from dictionary."""
        return cls(variables=config)
