from dataclasses import dataclass

from dagster_graphql import DagsterGraphQLClient

from vulkan_engine.backends.dagster.trigger_run import create_dagster_client


@dataclass
class DagsterServiceConfig:
    """Configuration for connecting to Dagster service."""

    host: str
    port: str
    server_port: str

    @property
    def server_url(self) -> str:
        """Get server URL for Dagster service."""
        return f"http://{self.host}:{self.server_port}"


def create_dagster_client_from_config(
    config: DagsterServiceConfig,
) -> DagsterGraphQLClient:
    """Create Dagster client from configuration."""
    try:
        port = int(config.port)
    except ValueError:
        raise ValueError("Dagster port must be an integer")

    return create_dagster_client(config.host, port)
