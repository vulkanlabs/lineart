import json
from io import BytesIO
from typing import Any

from fastapi import Response
from requests import Request, Session
from vulkan.backtest.definitions import SupportedFileFormat

from vulkan_server.exceptions import raise_interservice_error
from vulkan_server.logger import init_logger

logger = init_logger("services")


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
