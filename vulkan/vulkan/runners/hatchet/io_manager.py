import json
import time
from typing import Any, Dict, Optional

from vulkan.core.step_metadata import StepMetadata

METADATA_OUTPUT_KEY = "metadata"
PUBLISH_IO_MANAGER_KEY = "hatchet_publish_io_manager"


class HatchetIOManager:
    """I/O manager for Hatchet data persistence."""

    def __init__(self, server_url: str):
        self.server_url = server_url

    def store_metadata(self, metadata: StepMetadata, run_id: str) -> bool:
        """Store step metadata."""
        import requests

        try:
            url = f"{self.server_url}/runs/{run_id}/metadata"
            response = requests.post(url, json=metadata.to_dict())
            return response.status_code in {200, 201}
        except Exception:
            return False

    def store_data(self, data: Any, key: str, run_id: str) -> bool:
        """Store arbitrary data."""
        import requests

        try:
            url = f"{self.server_url}/runs/{run_id}/data"
            payload = {
                "key": key,
                "data": data
                if isinstance(data, (dict, list, str, int, float, bool))
                else str(data),
                "timestamp": time.time(),
            }
            response = requests.post(url, json=payload)
            return response.status_code in {200, 201}
        except Exception:
            return False


class HatchetPublishIOManager(HatchetIOManager):
    """I/O manager for publishing metadata and results."""

    def handle_output(self, context: Any, obj: Any) -> None:
        """Handle output from Hatchet tasks."""
        if isinstance(obj, StepMetadata):
            run_id = getattr(context, "run_id", None)
            if run_id:
                self.store_metadata(obj, run_id)
        else:
            # Handle other output types as needed
            pass
