import base64
import os

from vulkan.cli.context import Context
from vulkan.spec.environment.packing import pack_workspace


def create_component(ctx: Context, name: str) -> str:
    response = ctx.session.post(
        f"{ctx.server_url}/components",
        json={"name": name},
    )
    assert (
        response.status_code == 200
    ), f"Failed to create component version: {response.content}"
    data = response.json()
    ctx.logger.debug(data)
    component_id = data["component_id"]

    return component_id


def create_component_version(
    ctx: Context,
    component_id: str,
    version_name: str,
    repository_path: str,
):
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Path is not a directory: {repository_path}")

    repository_path = pack_workspace(component_id, repository_path)
    ctx.logger.info(f"Creating component version {version_name}")
    response = ctx.session.post(
        f"{ctx.server_url}/components/{component_id}/versions",
        json={
            "version_name": version_name,
            "repository": base64.b64encode(repository_path).decode("ascii"),
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create component version: {response.content}"

    ctx.logger.info("Component version was successfully created.")
    return response.json()
