"""
Request preparation utilities for data sources.

Handles template resolution, field configuration, and auth merging
in a standardized way across test and production flows.
"""

from dataclasses import dataclass
from typing import Any

from vulkan.auth import AuthConfig
from vulkan.node_config import configure_fields, resolve_template

from vulkan_engine.services.auth_handler import AuthHandler


@dataclass
class PreparedRequest:
    """Prepared request fields ready for execution."""

    url: str
    headers: dict[str, str]
    params: dict[str, Any]
    body: dict | None
    method: str
    timeout: int | None = None


def prepare_request_fields(
    config: dict,
    local_variables: dict,
    env_variables: dict,
    method: str = "GET",
    timeout: int | None = None,
) -> PreparedRequest:
    """
    Prepare request fields by resolving templates

    Resolves Jinja2 templates in URL, headers, params, and body using
    provided variables.

    Args:
        config: HTTP configuration (url, headers, params, body)
        local_variables: Runtime params for template resolution
        env_variables: Env vars for template resolution
        method: HTTP method
        timeout: Request timeout in seconds

    Returns:
        PreparedRequest with resolved fields
    """
    url = resolve_template(config.get("url", ""), local_variables, env_variables)
    headers = configure_fields(
        config.get("headers") or {}, local_variables, env_variables
    )
    params = configure_fields(
        config.get("params") or {}, local_variables, env_variables
    )

    body = None
    if config.get("body"):
        body = configure_fields(config["body"], local_variables, env_variables)

    return PreparedRequest(
        url=url,
        headers=headers,
        params=params,
        body=body,
        method=method,
        timeout=timeout,
    )


def add_auth_headers(
    prepared: PreparedRequest,
    auth_config: AuthConfig | None,
    data_source_id: str,
    credentials: dict[str, str],
    cache=None,
) -> PreparedRequest:
    """
    Add authentication headers to prepared request

    Creates an AuthHandler to generate auth headers and merges them with
    the existing headers

    Args:
        prepared: PreparedRequest
        auth_config: Authentication configuration
        data_source_id: Data source ID (for cache key)
        credentials: Auth credentials (CLIENT_ID, CLIENT_SECRET, etc.)
        cache: Optional cache (Redis) for token caching

    Returns:
        PreparedRequest with auth headers added
    """
    if not auth_config:
        return prepared

    auth_handler = AuthHandler(
        auth_config=auth_config,
        data_source_id=data_source_id,
        credentials=credentials,
        cache=cache,
    )

    auth_headers = auth_handler.get_auth_headers()
    prepared.headers = {**prepared.headers, **auth_headers}

    return prepared
