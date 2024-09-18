import base64
import os

import click
import yaml

from vulkan.cli.context import Context, pass_context
from vulkan.environment.config import VulkanWorkspaceConfig
from vulkan.environment.packing import pack_workspace


@click.command()
@pass_context
@click.option("--policy_id", type=str, required=True, help="Id of the policy")
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--repository_path", type=str, required=True, help="Path to repository")
def create_policy_version(
    ctx: Context,
    policy_id: int,
    version_name: str,
    repository_path: str,
):
    # TODO: at the moment we assume repository is a path in local disk,
    # but this could be a remote repository in git etc
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Path is not a directory: {repository_path}")

    if not os.path.exists(repository_path):
        msg = f"Path does not exist - resolved to: {repository_path}"
        raise FileNotFoundError(msg)
    if not os.path.isdir(repository_path):
        msg = f"Path is not a directory - resolved to: {repository_path}"
        raise ValueError(msg)

    # TODO: check that the code path is a valid python package or module
    config_path = os.path.join(repository_path, "vulkan.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    with open(config_path, "r") as fn:
        config_data = yaml.safe_load(fn)

    # TODO: we aren't currently usign this, but it can become handy in the future
    # to validate the user config
    _ = VulkanWorkspaceConfig.from_dict(config_data)

    repository = pack_workspace(version_name, repository_path)
    ctx.logger.info(f"Creating workspace {version_name}")

    body = {
        "policy_id": policy_id,
        "alias": version_name,
        "repository": base64.b64encode(repository).decode("ascii"),
        "repository_version": "0.0.1",  # TODO: get/gen a hash
    }

    # TODO: send repository as file upload
    response = ctx.session.post(
        f"{ctx.server_url}/policies/{policy_id}/versions",
        json=body,
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create policy version: {response.content}")

    policy_version_id = response.json()["policy_version_id"]
    ctx.logger.debug(response.json())
    ctx.logger.info(
        f"Created workspace {version_name} with policy version {policy_version_id}"
    )
    return policy_version_id
