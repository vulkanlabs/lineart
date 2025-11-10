"""HTTP client with retry logic and response parsing."""

import csv
import io
import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from vulkan.connections import HTTPConfig
from vulkan.node_config import configure_fields, resolve_template


class HTTPClientError(Exception):
    """Base exception for HTTP client errors."""

    def __init__(self, message: str, status_code: int | None = None):
        self.status_code = status_code
        super().__init__(message)


def _xml_to_dict(element: ET.Element) -> dict | str:
    """Convert XML element to dictionary with improved handling.

    Args:
        element: XML element to convert

    Returns:
        Dictionary representation of the XML element, or string if text-only
    """
    result = {}

    if element.attrib:
        result["@attributes"] = element.attrib

    if element.text and element.text.strip():
        if len(element) == 0 and not element.attrib:
            return element.text.strip()
        else:
            result["text"] = element.text.strip()

    for child in element:
        child_data = _xml_to_dict(child)
        if child.tag in result:
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    return result if result else ""


class HTTPClient:
    """Handles HTTP requests with retry logic and response parsing."""

    def __init__(self, config: HTTPConfig):
        """Initialize HTTP client with configuration.

        Args:
            config: HTTP configuration including URL, method, headers, etc.
        """
        self.config = config

    def _parse_response(self, response: httpx.Response) -> Any:
        """Parse HTTP response based on configured response type.

        Args:
            response: HTTP response object

        Returns:
            Parsed response data

        Raises:
            HTTPClientError: If parsing fails
        """
        response_type = self.config.response_type

        parsers: dict[str, Callable[[httpx.Response], Any]] = {
            "JSON": lambda r: r.json(),
            "XML": lambda r: _xml_to_dict(ET.fromstring(r.text)),
            "CSV": lambda r: list(csv.DictReader(io.StringIO(r.text))),
            "PLAIN_TEXT": lambda r: r.text,
        }

        if response_type not in parsers:
            raise HTTPClientError(f"Unsupported response type: {response_type}")

        try:
            return parsers[response_type](response)
        except Exception as e:
            raise HTTPClientError(
                f"Failed to parse response as {response_type}: {e}"
            ) from e

    def execute_raw(
        self,
        local_variables: dict,
        env_variables: dict,
        extra_headers: dict | None = None,
        extra_params: dict | None = None,
    ) -> httpx.Response:
        """Execute HTTP request and return raw httpx.Response object.

        Args:
            local_variables: Runtime parameters for template resolution
            env_variables: Environment variables for template resolution
            extra_headers: Additional headers (e.g., authentication headers)
            extra_params: Additional query parameters (e.g., API keys)

        Returns:
            Raw httpx.Response object

        Raises:
            HTTPClientError: If request fails
        """
        url = resolve_template(self.config.url, local_variables, env_variables)
        headers = configure_fields(self.config.headers, local_variables, env_variables)
        params = configure_fields(self.config.params, local_variables, env_variables)
        body = configure_fields(self.config.body, local_variables, env_variables)

        if extra_headers:
            headers = {**extra_headers, **headers}
        if extra_params:
            params = {**extra_params, **params}

        retry_config = self.config.retry

        @retry(
            stop=stop_after_attempt(retry_config.max_retries + 1),
            wait=wait_exponential(multiplier=retry_config.backoff_factor or 1.0),
            retry=retry_if_exception_type(httpx.HTTPStatusError),
            reraise=True,
        )
        def _make_request() -> httpx.Response:
            with httpx.Client(timeout=self.config.timeout) as client:
                response = client.request(
                    method=self.config.method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=body or None,
                )

                if (
                    retry_config.status_forcelist
                    and response.status_code in retry_config.status_forcelist
                ):
                    raise httpx.HTTPStatusError(
                        f"Retry on status {response.status_code}",
                        request=response.request,
                        response=response,
                    )

                response.raise_for_status()
                return response

        try:
            return _make_request()
        except httpx.HTTPStatusError as e:
            raise HTTPClientError(
                f"HTTP request failed with status {e.response.status_code}: {e.response.text}",
                status_code=e.response.status_code,
            ) from e
        except httpx.HTTPError as e:
            raise HTTPClientError(f"HTTP request failed: {e}") from e
        except Exception as e:
            raise HTTPClientError(f"Request execution failed: {e}") from e

    def execute(
        self,
        local_variables: dict,
        env_variables: dict,
        extra_headers: dict | None = None,
        extra_params: dict | None = None,
    ) -> Any:
        """Execute HTTP request and return parsed response data.

        Args:
            local_variables: Runtime parameters for template resolution
            env_variables: Environment variables for template resolution
            extra_headers: Additional headers (e.g., authentication headers)
            extra_params: Additional query parameters (e.g., API keys)

        Returns:
            Parsed response data

        Raises:
            HTTPClientError: If request fails or parsing fails
        """
        response = self.execute_raw(
            local_variables, env_variables, extra_headers, extra_params
        )
        return self._parse_response(response)
