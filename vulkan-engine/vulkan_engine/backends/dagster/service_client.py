from dataclasses import dataclass
from typing import Any

from requests import Request, Response, Session

from vulkan_engine.backends.dagster.trigger_run import update_repository
from vulkan_engine.backends.service_client import BackendServiceClient
from vulkan_engine.exceptions import raise_interservice_error
from vulkan_engine.logging import get_logger


@dataclass
class VulkanDagsterRequestConfig:
    headers: dict[str, Any] | None = None
    timeout: int | None = None


class DagsterServiceClient(BackendServiceClient):
    """Client to interact with the Vulkan Dagster service."""

    def __init__(
        self,
        server_url: str,
        dagster_client: Any,
        request_config: VulkanDagsterRequestConfig | None = None,
    ) -> None:
        self.server_url = server_url
        self.dagster_client = dagster_client
        self.session = Session()
        self.logger = get_logger(__name__)

        if request_config is None:
            self.request_config = VulkanDagsterRequestConfig()

    def update_workspace(
        self,
        workspace_id: str,
        spec: dict | None = None,
        requirements: list[str] | None = None,
    ) -> Response:
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
        response = self._make_request(
            method="GET",
            url=f"/workspaces/{workspace_id}",
            on_error="Failed to get workspace",
            json=None,
        )
        return response

    def delete_workspace(self, workspace_id: str) -> Response:
        response = self._make_request(
            method="DELETE",
            url=f"/workspaces/{workspace_id}",
            on_error="Failed to delete workspace",
            json=None,
        )
        return response

    def _make_request(
        self, method: str, url: str, json: dict | None, on_error: str
    ) -> Response:
        request = Request(
            method=method,
            url=f"{self.server_url}/{url}",
            headers=self.request_config.headers,
            json=json,
        ).prepare()
        response = self.session.send(request, timeout=self.request_config.timeout)

        if response.status_code != 200:
            raise_interservice_error(self.logger, response, on_error)

        return response

    def ensure_workspace_added(self, workspace_id: str) -> None:
        loaded_repos = update_repository(self.dagster_client)
        repo_loaded = loaded_repos.get(workspace_id, False)
        if not repo_loaded:
            msg = (
                f"Failed to load repository {workspace_id}.\n"
                f"Repository load status: {loaded_repos}\n"
            )
            raise ValueError(msg)

    def ensure_workspace_removed(self, workspace_id: str) -> None:
        loaded_repos = update_repository(self.dagster_client)
        if loaded_repos.get(workspace_id, None) is not None:
            msg = (
                f"Failed to remove repository {workspace_id}.\n"
                f"Repository load status: {loaded_repos}"
            )
            raise ValueError(msg)
