from urllib.parse import urlparse

from dagster_graphql import DagsterGraphQLClient


def create_dagster_client_from_url(
    url: str,
) -> DagsterGraphQLClient:
    """Create Dagster client from configuration."""
    parsed = urlparse(url)
    if parsed.hostname is None:
        raise ValueError(f"Invalid worker URL: {url}")
    if parsed.port is None:
        raise ValueError(f"Invalid worker URL: {url}")
    return DagsterGraphQLClient(parsed.hostname, port_number=parsed.port)
