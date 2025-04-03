from fastapi import Depends, Response
from requests import Request, Session

from vulkan_server import definitions
from vulkan_server.exceptions import raise_interservice_error
from vulkan_server.logger import init_logger

logger = init_logger("services")


class ResolutionServiceClient:
    """Client to interact with the resolution service."""

    def __init__(
        self,
        server_url: str,
    ) -> None:
        self.server_url = server_url
        self.session = Session()

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
        )
        return response

    def _make_request(
        self, method: str, url: str, json: dict, on_error: str
    ) -> Response:
        request = Request(
            method=method,
            url=f"{self.server_url}/{url}",
            json=json,
        ).prepare()
        response = self.session.send(request)

        if response.status_code != 200:
            raise_interservice_error(logger, response, on_error)

        return response


def get_resolution_service_client(
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
) -> ResolutionServiceClient:
    return ResolutionServiceClient(
        server_url=server_config.resolution_service_url,
    )
