from dataclasses import dataclass
from io import BytesIO
from typing import Any

from fastapi import Depends, Response
from requests import JSONDecodeError, Request, Session
from vulkan.backtest.definitions import SupportedFileFormat
from vulkan_public.exceptions import UNHANDLED_ERROR_NAME, VULKAN_INTERNAL_EXCEPTIONS

from vulkan_server import definitions
from vulkan_server.auth import get_project_id
from vulkan_server.dagster.client import get_dagster_client
from vulkan_server.dagster.trigger_run import _update_repository
from vulkan_server.logger import init_logger

logger = init_logger("services")


@dataclass
class VulkanDagsterRequestConfig:
    headers: dict[str, Any] | None = None
    timeout: int | None = None


class VulkanDagsterServerClient:
    """Client to interact with the Vulkan Dagster server."""

    def __init__(
        self,
        project_id: str,
        server_url: str,
        dagster_client: str,
        request_config: VulkanDagsterRequestConfig | None = None,
    ) -> None:
        self.project_id = project_id
        self.server_url = server_url
        self.dagster_client = dagster_client
        self.session = Session()

        if request_config is None:
            self.request_config = VulkanDagsterRequestConfig()

    def create_component_version(
        self, component_version_alias: str, repository: str
    ) -> Response:
        response = self._make_request(
            method="POST",
            url="/components",
            json={
                "alias": component_version_alias,
                "repository": repository,
                "project_id": self.project_id,
            },
            on_error="Failed to create component version",
        )
        return response

    def delete_component_version(self, component_version_alias: str) -> Response:
        response = self._make_request(
            method="POST",
            url="/components/delete",
            json={
                "alias": component_version_alias,
                "project_id": self.project_id,
            },
            on_error="Failed to delete component version",
        )
        return response

    def create_workspace(self, name: str, repository: str, components: list[str]) -> Response:
        response = self._make_request(
            method="POST",
            url="/workspaces/create",
            json={
                "name": name,
                "repository": repository,
                "project_id": self.project_id,
                "required_components": components,
            },
            on_error="Failed to create workspace",
        )
        return response

    def delete_workspace(self, name: str) -> Response:
        response = self._make_request(
            method="POST",
            url="/workspaces/delete",
            json={
                "name": name,
                "project_id": self.project_id,
            },
            on_error="Failed to delete workspace",
        )
        return response

    def _make_request(
        self, method: str, url: str, json: dict, on_error: str
    ) -> Response:
        request = Request(
            method=method,
            url=f"{self.server_url}/{url}",
            headers=self.request_config.headers,
            json=json,
        ).prepare()
        response = self.session.send(request, timeout=self.request_config.timeout)

        if response.status_code != 200:
            _raise_interservice_error(response, on_error)

        return response

    # TODO: this bit should be dagster-specific
    def update_repository(self, version_name: str) -> None:
        loaded_repos = _update_repository(self.dagster_client)
        if loaded_repos.get(version_name, False) is False:
            msg = (
                f"Failed to load repository {version_name}.\n"
                f"Repository load status: {loaded_repos}"
            )
            raise ValueError(msg)


def get_dagster_service_client(
    project_id: str = Depends(get_project_id),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
    dagster_client=Depends(get_dagster_client),
) -> VulkanDagsterServerClient:
    return VulkanDagsterServerClient(
        project_id=project_id,
        server_url=server_config.vulkan_dagster_server_url,
        dagster_client=dagster_client,
    )


class ResolutionServiceClient:
    """Client to interact with the resolution service."""

    def __init__(
        self,
        project_id: str,
        server_url: str,
    ) -> None:
        self.project_id = project_id
        self.server_url = server_url
        self.session = Session()

    def create_component_version(
        self, component_version_alias: str, repository: str
    ) -> Response:
        response = self._make_request(
            method="POST",
            url="/components",
            json={
                "alias": component_version_alias,
                "repository": repository,
                "project_id": self.project_id,
            },
            on_error="Failed to create component version",
        )
        return response

    def delete_component_version(self, component_version_alias: str) -> Response:
        response = self._make_request(
            method="POST",
            url="/components/delete",
            json={
                "alias": component_version_alias,
                "project_id": self.project_id,
            },
            on_error="Failed to delete component version",
        )
        return response

    def create_workspace(
        self, name: str, repository: str
    ) -> Response:
        response = self._make_request(
            method="POST",
            url="/workspaces/create",
            json={
                "name": name,
                "repository": repository,
                "project_id": self.project_id,
            },
            on_error="Failed to create workspace",
        )
        return response

    def delete_workspace(self, name: str) -> Response:
        response = self._make_request(
            method="POST",
            url="/workspaces/delete",
            json={
                "name": name,
                "project_id": self.project_id,
            },
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
            _raise_interservice_error(response, on_error)

        return response


def _raise_interservice_error(response: Response, message: str) -> None:
    try:
        detail = response.json()["detail"]
        error_msg = f"{message}: {detail}"
    except (JSONDecodeError, KeyError):
        error_msg = f"{message}: {UNHANDLED_ERROR_NAME}"

    if detail["error"] == "VulkanInternalException":
        logger.error(f"Got err: {detail}")
        _exception = VULKAN_INTERNAL_EXCEPTIONS[detail["exit_status"]]
        raise _exception(msg=detail["msg"])

    raise ValueError(error_msg)


def get_resolution_service_client(
    project_id: str = Depends(get_project_id),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
) -> ResolutionServiceClient:
    return ResolutionServiceClient(
        project_id=project_id,
        server_url=server_config.resolution_service_url,
    )


class VulkanFileIngestionServiceClient:
    """Client to interact with the file ingestion service."""

    def __init__(self, project_id: str, server_url: str) -> "None":
        self.project_id = project_id
        self.server_url = server_url
        self.session = Session()

    def validate_and_publish(
        self,
        file_format: SupportedFileFormat,
        content,
        schema: str,
    ) -> tuple[Any, bool]:
        logger.info("Making request to validate and publish file")
        response = self._make_request(
            method="POST",
            url="/file",
            params={
                "project_id": self.project_id,
                "file_format": file_format.value,
                "schema": str(schema),
            },
            files={
                "input_file": BytesIO(content),
            },
            on_error="Failed to upload data",
        )
        file_info = response.json()
        return file_info

    def _make_request(
        self,
        method: str,
        url: str,
        on_error: str,
        json: dict | None = None,
        files: dict | None = None,
        params: dict | None = None,
    ) -> Response:
        request = Request(
            method=method,
            url=f"{self.server_url}/{url}",
            # headers=self.request_config.headers,
            json=json,
            params=params,
            files=files,
        ).prepare()
        response = self.session.send(request)
        logger.warning(f"content: {response.content}")

        if response.status_code != 200:
            _raise_interservice_error(response, on_error)

        return response
