import csv
import io
import json
import xml.etree.ElementTree as ET
from enum import Enum

import requests
from pydantic import BaseModel
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from vulkan.node_config import ConfigurableDict, configure_fields, resolve_template


class RetryPolicy(BaseModel):
    max_retries: int
    backoff_factor: float | None = None
    status_forcelist: list[int] | None = None


class ResponseType(Enum):
    JSON = "JSON"
    XML = "XML"
    CSV = "CSV"
    PLAIN_TEXT = "PLAIN_TEXT"


class HTTPConfig(BaseModel):
    url: str
    method: str = "GET"
    headers: ConfigurableDict | None = dict()
    params: ConfigurableDict | None = dict()
    body: ConfigurableDict | None = dict()
    timeout: int | None = None
    retry: RetryPolicy | None = RetryPolicy(max_retries=1)
    response_type: str | None = ResponseType.PLAIN_TEXT.value

    def __post_init__(self):
        # TODO: Validate url
        pass


def make_request(
    config: HTTPConfig, local_variables: dict, env_variables: dict
) -> requests.PreparedRequest:
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

    headers = configure_fields(config.headers, local_variables, env_variables)
    params = configure_fields(config.params, local_variables, env_variables)
    body = configure_fields(config.body, local_variables, env_variables)

    if config.headers.get("Content-Type") == "application/json":
        json = body
        data = None
    else:
        json = None
        data = body

    req = requests.Request(
        url=url,
        method=config.method,
        headers=headers,
        params=params,
        data=data,
        json=json,
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
