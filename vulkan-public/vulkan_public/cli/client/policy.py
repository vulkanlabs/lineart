import base64
import os

import yaml

from vulkan_public.cli.context import Context
from vulkan_public.exceptions import UserImportException
from vulkan_public.spec.environment.config import UserWorkspaceConfig
from vulkan_public.spec.environment.loaders import load_policy_definition
from vulkan_public.spec.environment.packing import (
    find_package_entrypoint,
    pack_workspace,
)


def list_policies(ctx: Context, include_archived: bool = False):
    response = ctx.session.get(
        f"{ctx.server_url}/policies", params={"include_archived": include_archived}
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list policies: {response.content}")
    return response.json()


def create_policy(
    ctx: Context,
    name: str,
    input_schema: str,
    output_schema: str,
    description: str = "",
):
    response = ctx.session.post(
        f"{ctx.server_url}/policies",
        json={
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "output_schema": output_schema,
        },
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create policy: {response.content}")

    policy_id = response.json()["policy_id"]
    ctx.logger.info(f"Created policy {name} with id {policy_id}")
    return policy_id


def set_active_version(ctx: Context, policy_id: str, policy_version_id: str):
    response = ctx.session.put(
        f"{ctx.server_url}/policies/{policy_id}",
        json={"active_policy_version_id": policy_version_id},
    )
    if response.status_code != 200:
        raise ValueError("Failed to activate policy version")


def unset_active_version(ctx: Context, policy_id: str):
    response = ctx.session.put(
        f"{ctx.server_url}/policies/{policy_id}",
        json={"active_policy_version_id": None},
    )
    if response.status_code != 200:
        raise ValueError("Failed to unset active version")


def delete_policy(ctx: Context, policy_id: str):
    response = ctx.session.delete(f"{ctx.server_url}/policies/{policy_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to delete policy: {response.content}")
    ctx.logger.info(f"Deleted policy {policy_id}")


def list_runs_by_policy(ctx: Context, policy_id: str):
    response = ctx.session.get(f"{ctx.server_url}/policies/{policy_id}/runs")
    if response.status_code != 200:
        raise ValueError(f"Failed to list runs: {response.content}")
    return response.json()


def list_policy_versions(ctx: Context, policy_id: str, include_archived: bool = False):
    response = ctx.session.get(
        f"{ctx.server_url}/policies/{policy_id}/versions",
        params={"include_archived": include_archived},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list policy versions: {response.content}")
    return response.json()


def create_policy_version(
    ctx: Context,
    policy_id: str,
    version_name: str,
    repository_path: str,
):
    # TODO: at the moment we assume repository is a path in local disk,
    # but this could be a remote repository in git etc
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Repository path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Repository path is not a directory: {repository_path}")

    # TODO: check that the code path is a valid python package or module
    pyproject_path = os.path.join(repository_path, "pyproject.toml")
    if not os.path.exists(pyproject_path):
        raise FileNotFoundError(
            f"File pyproject.toml not found in path: {repository_path}/.\n"
            "A pyproject.toml file must be specified at the root level of the repository."
        )

    config_path = os.path.join(repository_path, "vulkan.yaml")
    if not os.path.exists(config_path):
        raise FileNotFoundError(
            f"Config file not found: {config_path}.\n"
            "A vulkan.yaml file must be specified at the root level of the repository."
        )

    with open(config_path, "r") as fn:
        config_data = yaml.safe_load(fn)

    # TODO: we aren't currently usign this, but it can become handy in the future
    # to validate the user config
    _ = UserWorkspaceConfig.from_dict(config_data)

    try:
        entrypoint = find_package_entrypoint(repository_path)
    except ValueError as e:
        raise ValueError(
            f"Failed to find entrypoint in repository: {repository_path}\n{e}"
        )

    try:
        _ = load_policy_definition(entrypoint)
    except UserImportException as e:
        ctx.logger.warning("Failed to import module from entrypoint.")
        ctx.logger.warning(str(e))

    repository = pack_workspace(version_name, repository_path)
    # TODO: improve UX by showing a loading animation
    ctx.logger.info(f"Creating workspace {version_name}. This may take a while...")

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
    if response.status_code == 400:
        detail = response.json().get("detail", {})
        error = detail.get("error")
        if error == "ComponentNotFoundException":
            raise ValueError(
                "Missing components. Please install the following components "
                f"and try again: {detail['metadata']['components']}"
            )
        if error == "DefinitionNotFoundException":
            raise ValueError(
                "No PolicyDefinition instance was found in the specified "
                "repository. Make sure it is accessible on the configured "
                "entrypoint (imported on __init__.py, if mode=python_package)."
            )
        if error == "InvalidDefinitionError":
            ctx.logger.debug(detail)
            raise ValueError(
                "The PolicyDefinition instance was improperly configured. "
                "It may be missing a node or have missing/invalid attributes. "
                "It could also be that an imported python package wasn't specified "
                "as a dependency in the pyproject.toml file."
            )
        if error == "ConflictingDefinitionsError":
            raise ValueError(
                "More than one PolicyDefinition instances was found in the "
                "specified repository."
            )
        raise ValueError(f"Bad request: {detail}")

    if response.status_code != 200:
        raise ValueError(f"Failed to create policy version: {response.content}")

    policy_version_id = response.json()["policy_version_id"]
    ctx.logger.debug(response.json())
    ctx.logger.info(
        f"Created workspace {version_name} with policy version {policy_version_id}"
    )
    return policy_version_id


def delete_policy_version(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.delete(
        f"{ctx.server_url}/policy-versions/{policy_version_id}"
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to delete policy version: {response.content}")
    ctx.logger.info(f"Deleted policy version {policy_version_id}")


def get_policy_version_graph(ctx: Context, policy_version_id: str):
    response = ctx.session.get(f"{ctx.server_url}/policy-versions/{policy_version_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to get policy version graph: {response.content}")
    return response.json()["graph_definition"]
