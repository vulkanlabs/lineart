from urllib.parse import urlparse

from dagster_graphql import DagsterGraphQLClient

from vulkan_engine.backends.dagster.trigger_run import create_dagster_client


def create_dagster_client_from_url(
    url: str,
) -> DagsterGraphQLClient:
    """Create Dagster client from configuration."""
    parsed = urlparse(url)
    if parsed.hostname is None:
        raise ValueError(f"Invalid worker URL: {url}")
    if parsed.port is None:
        raise ValueError(f"Invalid worker URL: {url}")
    return create_dagster_client(parsed.hostname, parsed.port)
