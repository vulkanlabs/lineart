import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from vulkan_public.schemas import (
    DataSourceSpec,
    EnvVarConfig,
)


def make_request(spec: DataSourceSpec, body: dict, variables: dict) -> requests.Request:
    if spec.request.headers.get("Content-Type") == "application/json":
        json = body
        data = None
    else:
        json = None
        data = body

    retry = Retry(
        total=spec.retry.max_retries,
        backoff_factor=spec.retry.backoff_factor,
        status_forcelist=spec.retry.status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = _configure_fields(spec.request.headers, variables)
    params = _configure_fields(spec.request.params, variables)

    req = requests.Request(
        method=spec.request.method,
        url=spec.request.url,
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
