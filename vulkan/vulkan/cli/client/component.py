import base64
import os

from vulkan.cli.context import Context
from vulkan.spec.component import component_version_alias
from vulkan.environment.packing import pack_workspace


def create_component(ctx: Context, name: str) -> str:
    response = ctx.session.post(
        f"{ctx.server_url}/components",
        json={"name": name},
    )
    ctx.logger.debug(response.json())
    data = response.json()
    ctx.logger.debug(data)
    component_id = data["component_id"]

    return component_id


def create_component_version(
    ctx: Context,
    component_id: str,
    component_name: str,
    version: str,
    repository_path: str,
):
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Path is not a directory: {repository_path}")

    alias = component_version_alias(component_name, version)

    repository_path = pack_workspace(alias, repository_path)
    ctx.logger.info(f"Creating component {component_name}")
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

    ctx.logger.info(f"Created component {component_name}-{version}")
    return response.json()
