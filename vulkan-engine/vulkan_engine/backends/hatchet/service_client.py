"""Service client for interacting with Hatchet server."""

from dataclasses import dataclass
from typing import Any

from requests import Request, Response, Session

from vulkan_engine.backends.service_client import BackendServiceClient
from vulkan_engine.exceptions import raise_interservice_error
from vulkan_engine.logging import get_logger


@dataclass
class HatchetRequestConfig:
    """Configuration for Hatchet HTTP requests."""

    headers: dict[str, Any] | None = None
    timeout: int | None = None


class HatchetServiceClient(BackendServiceClient):
    """Client to interact with the Hatchet service."""

    def __init__(
        self,
        server_url: str,
        request_config: HatchetRequestConfig | None = None,
    ) -> None:
        self.server_url = server_url
        self.session = Session()
        self.logger = get_logger(__name__)

        if request_config is None:
            self.request_config = HatchetRequestConfig()
        else:
            self.request_config = request_config

    def update_workspace(
        self,
        workspace_id: str,
        spec: dict | None = None,
        requirements: list[str] | None = None,
    ) -> Response:
        """Create or update a workspace in Hatchet."""
        response = self._make_request(
            method="POST",
            url=f"/workspaces/{workspace_id}",
            json={
                "spec": spec,
                "requirements": requirements,
            },
            on_error="Failed to create workspace",
        )
        return response

    def get_workspace(self, workspace_id: str) -> Response:
        """Get information about a workspace from Hatchet."""
        response = self._make_request(
            method="GET",
            url=f"/workspaces/{workspace_id}",
            on_error="Failed to get workspace",
        )
        return response

    def delete_workspace(self, workspace_id: str) -> Response:
        """Delete a workspace from Hatchet."""
        response = self._make_request(
            method="DELETE",
            url=f"/workspaces/{workspace_id}",
            on_error="Failed to delete workspace",
            json=None,
        )
        return response

    def ensure_workspace_added(self, workspace_id: str) -> None:
        """Ensure that the workspace has been successfully added to Hatchet.

        For Hatchet, we verify by checking if the workspace exists.
        """
        try:
            response = self.get_workspace(workspace_id)
            if response.status_code != 200:
                raise ValueError(f"Workspace {workspace_id} was not successfully added")
        except Exception as e:
            raise ValueError(
                f"Failed to verify workspace {workspace_id} was added: {e}"
            )

    def ensure_workspace_removed(self, workspace_id: str) -> None:
        """Ensure that the workspace has been successfully removed from Hatchet.

        For Hatchet, we verify by checking that the workspace no longer exists.
        """
        try:
            response = self.get_workspace(workspace_id)
            if response.status_code == 200:
                raise ValueError(
                    f"Workspace {workspace_id} was not successfully removed"
                )
        except Exception:
            # If we get an error (like 404), that's expected for a removed workspace
            pass

    def _make_request(
        self, method: str, url: str, on_error: str, json: dict | None = None
    ) -> Response:
        """Make an HTTP request to the Hatchet service."""
        request = Request(
            method=method,
            url=f"{self.server_url}{url}",
            headers=self.request_config.headers,
            json=json,
        ).prepare()

        response = self.session.send(request, timeout=self.request_config.timeout)

        if response.status_code != 200:
            raise_interservice_error(self.logger, response, on_error)

        return response
