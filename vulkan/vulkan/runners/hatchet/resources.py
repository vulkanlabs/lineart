from typing import Any, Dict, Optional

try:
    from hatchet_sdk import Hatchet

    HATCHET_AVAILABLE = True
except ImportError:
    HATCHET_AVAILABLE = False

    # Mock Hatchet class
    class Hatchet:
        def __init__(self, **kwargs):
            pass


from vulkan.runners.hatchet.run_config import HatchetRunConfig


def _check_hatchet_available():
    """Check if Hatchet SDK is available."""
    if not HATCHET_AVAILABLE:
        raise ImportError(
            "Hatchet SDK is not installed. Install it with: pip install hatchet-sdk"
        )


DATA_CLIENT_KEY = "hatchet_data_client"
RUN_CLIENT_KEY = "hatchet_run_client"
HATCHET_CLIENT_KEY = "hatchet_client"


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
            self._client = Hatchet(
                server_url=self.config.hatchet_server_url,
                token=self.config.hatchet_api_key,
                namespace=self.config.namespace,
            )
        return self._client


def create_hatchet_resources(config: HatchetRunConfig) -> Dict[str, Any]:
    """Create all Hatchet resources."""
    return {
        DATA_CLIENT_KEY: HatchetDataClient(config.server_url),
        RUN_CLIENT_KEY: HatchetRunClient(config.server_url),
        HATCHET_CLIENT_KEY: HatchetClientResource(config),
    }
