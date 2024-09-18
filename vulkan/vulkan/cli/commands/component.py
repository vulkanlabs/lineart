import base64
import os

import click

from vulkan.core.component import component_version_alias
from vulkan.environment.packing import pack_workspace
from vulkan.cli.context import Context, pass_context


@click.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the component")
@click.option(
    "--version", type=str, required=True, help="Alias for the version of the component"
)
@click.option("--repository_path", type=str, required=True, help="Path to repository")
def create_component(
    ctx: Context,
    name: str,
    version: str,
    repository_path: str,
):
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Path is not a directory: {repository_path}")

    response = ctx.session.post(
        f"{ctx.server_url}/components",
        json={"name": name},
    )
    ctx.logger.debug(response.json())
    data = response.json()
    ctx.logger.debug(data)
    component_id = data["component_id"]

    alias = component_version_alias(name, version)

    repository_path = pack_workspace(alias, repository_path)
    ctx.logger.info(f"Creating component {name}")
    response = ctx.session.post(
        f"{ctx.server_url}/components/{component_id}/versions",
        json={
            "alias": alias,
            "repository": base64.b64encode(repository_path).decode("ascii"),
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create component version: {response.content}"

    ctx.logger.info(f"Created component {name}-{version}")
    return response.json()
