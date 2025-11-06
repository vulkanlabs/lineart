import csv
import io
import json
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Literal

import requests
from pydantic import BaseModel, Field, field_validator
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from vulkan.node_config import (
    ConfigurableDict,
    configurable_dict_adapter,
    configure_fields,
    resolve_template,
)


class RetryPolicy(BaseModel):
    max_retries: int
    backoff_factor: float | None = None
    status_forcelist: list[int] | None = None


class ResponseType(Enum):
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"
    PLAIN_TEXT = "PLAIN_TEXT"


HTTPMethod = Literal["GET", "POST", "PUT", "DELETE"]


class HTTPConfig(BaseModel):
    """Configuration for an HTTP request with templated fields."""

    url: str
    method: HTTPMethod = "GET"
    headers: dict = Field(default_factory=dict)
    params: dict = Field(default_factory=dict)
    body: dict = Field(default_factory=dict)
    timeout: int | None = None
    retry: RetryPolicy = Field(default_factory=lambda: RetryPolicy(max_retries=1))
    response_type: Literal["JSON", "XML", "CSV", "PLAIN_TEXT"] = (
        ResponseType.PLAIN_TEXT.value
    )

    @field_validator("url")
    @classmethod
    def _validate_url(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("url must be a non-empty string")
        # Allow templated pieces but require explicit scheme at start
        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError("url must start with 'http://' or 'https://'")
        return v

    @field_validator("headers", "params", "body")
    @classmethod
    def _ensure_configurable_dict(cls, v) -> ConfigurableDict:
        """Validate that all dicts conform to our parameter specification.

        This is performed manually to avoid generation errors from
        OpenAPI spec to client code.
        """
        if v is None:
            return {}
        return configurable_dict_adapter.validate_python(v)


def make_request(
    config: HTTPConfig,
    local_variables: dict,
    env_variables: dict,
    extra_headers: dict | None = None,
    extra_params: dict | None = None,
) -> requests.PreparedRequest:
    """
    Creates a PreparedRequest from HTTPConfig.

    Args:
        config: HTTP configuration (url, method, headers, params, body, etc)
        local_variables: Runtime parameters for template resolution
        env_variables: Environment variables for template resolution
        extra_headers: Additional  (e.g., authentication headers).
        extra_params: Additional query parameters (e.g., API keys).

    Returns:
        PreparedRequest ready to be sent

    Example:
        # Without auth
        req = make_request(config, {}, {})

        # With auth headers
        auth_headers = {"Authorization": "Bearer token123"}
        req = make_request(config, {}, {}, extra_headers=auth_headers)
    """
    retry = Retry(
        total=config.retry.max_retries,
        backoff_factor=config.retry.backoff_factor,
        status_forcelist=config.retry.status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # Resolve URL with template variables
    url = resolve_template(config.url, local_variables, env_variables)

    # Configure base headers, params, body from config
    headers = configure_fields(config.headers, local_variables, env_variables)
    params = configure_fields(config.params, local_variables, env_variables)
    body = configure_fields(config.body, local_variables, env_variables)

    # auth comes first, config can override
    if extra_headers:
        headers = {**extra_headers, **headers}

    if extra_params:
        params = {**extra_params, **params}

    # Determine payload format
    if headers.get("Content-Type") == "application/json":
        json_payload = body
        data_payload = None
    else:
        json_payload = None
        data_payload = body

    # Create PreparedRequest
    req = requests.Request(
        url=url,
        method=config.method,
        headers=headers,
        params=params,
        data=data_payload,
        json=json_payload,
    ).prepare()
    return req


def format_response_data(value: bytes, response_type: str = "PLAIN_TEXT") -> dict | str:
    """Format the response data based on the specified format."""
    data = value.decode("utf-8")
    if response_type == ResponseType.JSON.value:
        return json.loads(data)
    elif response_type == ResponseType.XML.value:
        return _xml_to_dict(ET.fromstring(data))
    elif response_type == ResponseType.CSV.value:
        csv_reader = csv.DictReader(io.StringIO(data))
        return list(csv_reader)
    return data


def _xml_to_dict(element: ET.Element) -> dict:
    """Convert XML element to dictionary"""
    result = {}

    # Add attributes
    if element.attrib:
        result.update(element.attrib)

    # Add text content
    if element.text and element.text.strip():
        if len(element) == 0:  # No children
            return element.text.strip()
        else:
            result["text"] = element.text.strip()

    # Add children
    for child in element:
        child_data = _xml_to_dict(child)
        if child.tag in result:
            # Convert to list if multiple elements with same tag
            if not isinstance(result[child.tag], list):
                result[child.tag] = [result[child.tag]]
            result[child.tag].append(child_data)
        else:
            result[child.tag] = child_data

    return result
