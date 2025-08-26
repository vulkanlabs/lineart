from typing import Any, Dict, Optional

from hatchet_sdk import Hatchet

from vulkan.runners.hatchet.run_config import HatchetRunConfig

DATA_CLIENT_KEY = "hatchet_data_client"
RUN_CLIENT_KEY = "hatchet_run_client"


class HatchetDataClient:
    """Client for data operations in Hatchet context."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def get_data(
        self, data_source: str, configured_params: Dict[str, Any], run_id: str
    ):
        """Fetch data from data source."""
        import requests

        url = f"{self.server_url}/data/{data_source}"
        params = {"run_id": run_id, **configured_params}

        return requests.get(url, params=params)


class HatchetRunClient:
    """Client for run operations in Hatchet context."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def run_version_sync(
        self, policy_version_id: str, data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a policy version synchronously."""
        import requests

        url = f"{self.server_url}/policy-versions/{policy_version_id}/run"
        response = requests.post(url, json=data)
        response.raise_for_status()
        return response.json()


class HatchetClientResource:
    """Resource for Hatchet client management."""

    def __init__(self, config: HatchetRunConfig):
        self.config = config
        self._client: Optional[Hatchet] = None

    @property
    def client(self) -> Hatchet:
        """Get or create Hatchet client."""
        if self._client is None:
            from hatchet_sdk.config import ClientConfig

            # Create config with token and any explicitly provided values
            config = ClientConfig(
                token=self.config.hatchet_api_key,
                namespace=self.config.namespace,
            )

            # Only set server_url if explicitly provided
            if self.config.hatchet_server_url:
                config.server_url = self.config.hatchet_server_url

            self._client = Hatchet(config=config)
        return self._client


def create_hatchet_resources(config: HatchetRunConfig) -> Dict[str, Any]:
    """Create all Hatchet resources."""
    return {
        DATA_CLIENT_KEY: HatchetDataClient(config.server_url),
        RUN_CLIENT_KEY: HatchetRunClient(config.server_url),
    }
