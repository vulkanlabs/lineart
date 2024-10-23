import base64
import os

from vulkan_public.cli.context import Context
from vulkan_public.spec.environment.packing import pack_workspace


def list_components(ctx: Context, include_archived: bool = False):
    response = ctx.session.get(
        f"{ctx.server_url}/components",
        params={"include_archived": include_archived},
    )
    assert response.status_code == 200, f"Failed to list components: {response.content}"
    return response.json()


def create_component(ctx: Context, name: str) -> str:
    if " " in name:
        raise ValueError("Component name cannot contain spaces.")

    response = ctx.session.post(
        f"{ctx.server_url}/components",
        json={"name": name},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create component: {response.content}")

    component_id = response.json()["component_id"]
    ctx.logger.info(f"Created component {name} with id {component_id}")
    return component_id


def delete_component(ctx: Context, component_id: str):
    response = ctx.session.delete(f"{ctx.server_url}/components/{component_id}")
    assert (
        response.status_code == 200
    ), f"Failed to delete component: {response.content}"
    ctx.logger.info(f"Deleted component {component_id}")


def list_component_versions(
    ctx: Context, component_id: str, include_archived: bool = False
):
    response = ctx.session.get(
        f"{ctx.server_url}/components/{component_id}/versions",
        params={"include_archived": include_archived},
    )
    assert (
        response.status_code == 200
    ), f"Failed to list component versions: {response.content}"
    return response.json()


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

    component_version_id = response.json()["component_version_id"]
    ctx.logger.info(
        f"Created component version {component_version_id} ({version_name}) "
        f"for component {component_id}."
    )
    return component_version_id


def delete_component_version(
    ctx: Context,
    component_version_id: str,
):
    response = ctx.session.delete(
        f"{ctx.server_url}/component-versions/{component_version_id}"
    )
    assert (
        response.status_code == 200
    ), f"Failed to delete component version: {response.content}"
    ctx.logger.info(f"Deleted component version {component_version_id}")
