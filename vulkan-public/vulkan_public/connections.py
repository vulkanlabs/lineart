import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from vulkan_public.schemas import (
    EnvVarConfig,
    HTTPSourceSpec,
)


def make_request(
    source: HTTPSourceSpec, body: dict, variables: dict
) -> requests.Request:
    if source.headers.get("Content-Type") == "application/json":
        json = body
        data = None
    else:
        json = None
        data = body

    retry = Retry(
        total=source.retry.max_retries,
        backoff_factor=source.retry.backoff_factor,
        status_forcelist=source.retry.status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = _configure_fields(source.headers, variables)
    params = _configure_fields(source.params, variables)

    req = requests.Request(
        method=source.method,
        url=source.url,
        headers=headers,
        params=params,
        data=data,
        json=json,
    ).prepare()
    return req


def _configure_fields(spec: dict, variables: dict) -> dict:
    if spec is None:
        spec = {}

    for key, value in spec.items():
        if isinstance(value, EnvVarConfig):
            spec[key] = variables[value.env]

    return spec
