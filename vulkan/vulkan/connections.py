import csv
import io
import json
import xml.etree.ElementTree as ET
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from vulkan.node_config import (
    ConfigurableDict,
    configurable_dict_adapter,
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


def format_response_data(
    value: bytes, response_type: str = "PLAIN_TEXT"
) -> dict | str | list:
    """Format the response data based on the specified format.

    Args:
        value: Raw response bytes
        response_type: Type of response (JSON, XML, CSV, PLAIN_TEXT)

    Returns:
        Parsed response data
    """
    data = value.decode("utf-8")
    if response_type == ResponseType.JSON.value:
        return json.loads(data)
    elif response_type == ResponseType.XML.value:
        return _xml_to_dict(ET.fromstring(data))
    elif response_type == ResponseType.CSV.value:
        csv_reader = csv.DictReader(io.StringIO(data))
        return list(csv_reader)
    return data


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
