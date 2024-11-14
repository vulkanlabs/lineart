import json
from io import BytesIO
from typing import Any

from fastapi import Depends, Response
from requests import Request, Session
from vulkan.backtest.definitions import SupportedFileFormat

from vulkan_server import definitions
from vulkan_server.auth import get_project_id
from vulkan_server.exceptions import raise_interservice_error
from vulkan_server.logger import init_logger

logger = init_logger("services")


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

    def create_workspace(self, name: str, repository: str) -> Response:
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
            raise_interservice_error(logger, response, on_error)

        return response


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
        schema: dict,
    ) -> tuple[Any, bool]:
        logger.info("Making request to validate and publish file")
        response = self._make_request(
            method="POST",
            url="/file",
            params={
                "project_id": self.project_id,
                "file_format": file_format.value,
                "schema": json.dumps(schema),
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
            raise_interservice_error(logger, response, on_error)

        return response


class BeamLauncherClient:
    def __init__(self, project_id: str, server_url: str) -> None:
        self.project_id = project_id
        self.server_url = server_url
        self.session = Session()

    def launch_job(
        self,
        policy_version_id: str,
        backtest_id: str,
        image: str,
        data_sources: dict,
        config_variables: dict | None = None,
    ) -> Response:
        response = self._make_request(
            method="POST",
            url="/backtest/launch",
            json={
                "project_id": self.project_id,
                "policy_version_id": policy_version_id,
                "backtest_id": backtest_id,
                "image": image,
                "data_sources": data_sources,
                "config_variables": config_variables,
            },
            on_error="Failed to launch Beam job",
        )
        return response

    def _make_request(
        self,
        method: str,
        url: str,
        json: dict,
        on_error: str,
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


def get_beam_launcher_client(
    project_id: str = Depends(get_project_id),
    server_config: definitions.VulkanServerConfig = Depends(
        definitions.get_vulkan_server_config
    ),
) -> BeamLauncherClient:
    return BeamLauncherClient(
        project_id=project_id,
        server_url=server_config.beam_launcher_url,
    )
