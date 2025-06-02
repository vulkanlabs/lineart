import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from vulkan.data_source import EnvVarConfig, HTTPSource, RunTimeParam


def make_request(
    source: HTTPSource, node_variables: dict, env_variables: dict
) -> requests.PreparedRequest:
    retry = Retry(
        total=source.retry.max_retries,
        backoff_factor=source.retry.backoff_factor,
        status_forcelist=source.retry.status_forcelist,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session = requests.Session()
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    headers = _configure_fields(source.headers, node_variables, env_variables)
    params = _configure_fields(source.query_params, node_variables, env_variables)
    body = _configure_fields(source.body, node_variables, env_variables)

    if source.headers.get("Content-Type") == "application/json":
        json = body
        data = None
    else:
        json = None
        data = body

    req = requests.Request(
        method=source.method,
        url=source.url,
        headers=headers,
        params=params,
        data=data,
        json=json,
    ).prepare()
    return req


def _configure_fields(spec: dict, node_variables: dict, env_variables: dict) -> dict:
    if spec is None:
        spec = {}

    for key, value in spec.items():
        if isinstance(value, RunTimeParam):
            spec[key] = node_variables[value.param]
        if isinstance(value, EnvVarConfig):
            spec[key] = env_variables[value.env]

    return spec
