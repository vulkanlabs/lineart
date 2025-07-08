from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Response
from requests import Request, Session

from vulkan_engine import definitions
from vulkan_engine.dagster.client import get_dagster_client
from vulkan_engine.dagster.trigger_run import update_repository
from vulkan_engine.exceptions import raise_interservice_error
from vulkan_engine.logger import init_logger


@dataclass
class VulkanDagsterRequestConfig:
    headers: dict[str, Any] | None = None
    timeout: int | None = None


class VulkanDagsterServiceClient:
    """Client to interact with the Vulkan Dagster service."""

    def __init__(
        self,
        server_url: str,
        dagster_client: str,
        request_config: VulkanDagsterRequestConfig | None = None,
    ) -> None:
        self.server_url = server_url
        self.dagster_client = dagster_client
        self.session = Session()
        self.logger = init_logger("vulkan_dagster_service_client")

        if request_config is None:
            self.request_config = VulkanDagsterRequestConfig()

    def update_workspace(
        self,
        workspace_id: str,
        spec: dict,
        requirements: list[str],
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


def get_dagster_service_client(
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    dagster_client=Depends(get_dagster_client),
) -> VulkanDagsterServiceClient:
    return VulkanDagsterServiceClient(
        server_url=server_config.vulkan_dagster_server_url,
        dagster_client=dagster_client,
    )
