import base64
import logging
import os
from argparse import ArgumentParser

import requests
import yaml

from vulkan.dagster.workspace import pack_workspace
from vulkan.environment.config import ComponentVersionInfo, VulkanWorkspaceConfig

logging.basicConfig(level=logging.DEBUG)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    policy = subparsers.add_parser("create_policy", help="Create a policy")
    policy.add_argument("--name", type=str, required=True, help="Name of the policy")
    policy.add_argument(
        "--description", type=str, default="", help="Description of the policy"
    )

    workspace = subparsers.add_parser("create_workspace", help="Create a workspace")
    workspace.add_argument(
        "--policy_id", type=int, required=True, help="Id of the policy"
    )
    workspace.add_argument(
        "--name", type=str, required=True, help="Name of the workspace"
    )
    workspace.add_argument(
        "--repository_path", type=str, required=True, help="Path to repository"
    )
    
    component = subparsers.add_parser("create_component", help="Create a component")
    component.add_argument(
        "--name", type=str, required=True, help="Name of the component"
    )
    component.add_argument(
        "--version",
        type=str,
        required=True,
        help="Alias for the version of the component",
    )
    # TODO: demand input and output schemas after implementing logic in the server
    component.add_argument(
        "--input_schema",
        type=str,
        required=False,
        default="",
        help="Input schema of the component",
    )
    component.add_argument(
        "--output_schema",
        type=str,
        required=False,
        default="",
        help="Output schema of the component",
    )
    component.add_argument(
        "--repository_path", type=str, required=True, help="Path to repository"
    )

    args = parser.parse_args()

    # TODO: This should come from a user config
    SERVER_URL = "http://localhost:6001"

    if args.command == "create_policy":
        policy_id = create_policy(SERVER_URL, args.name, args.description, "")
        logging.info(f"Created policy {args.name} with id {policy_id}")

    elif args.command == "create_workspace":
        policy_id = args.policy_id
        policy_version_id = create_policy_version(
            SERVER_URL, policy_id, args.name, args.repository_path,
        )
        logging.info(
            f"Created workspace {args.name} with policy version {policy_version_id}"
        )
        register_active_version(SERVER_URL, policy_id, policy_version_id)

    elif args.command == "create_component":
        create_component(
            SERVER_URL,
            args.name,
            args.version,
            args.input_schema,
            args.output_schema,
            args.repository_path,
        )
        logging.info(f"Created component {args.name}")

    else:
        raise ValueError(f"Unknown command: {args.command}")


def config_environment():
    # TODO: create the config as a yaml file dynamically
    # so it can later be used to create / update the workspace.
    pass


def create_policy(server_url, name, description, input_schema):
    response = requests.post(
        f"{server_url}/policies",
        json={
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "output_schema": "",
        },
    )
    assert response.status_code == 200, "Failed to create policy"
    policy_id = response.json()["policy_id"]
    return policy_id


# TODO: at the moment we assume repository is a path in local disk,
# but this could be a remote repository in git etc
def create_policy_version(
    server_url: str,
    policy_id: int,
    version_name: str,
    repository_path: str,
):
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
    config = VulkanWorkspaceConfig.from_dict(config_data)

    repository = pack_workspace(version_name, repository_path)
    logging.info(f"Creating workspace {version_name}")

    body = {
        "config": {
            "policy_id": policy_id,
            "alias": version_name,
            "repository": base64.b64encode(repository).decode("ascii"),
            "repository_version": "0.0.1", # TODO: get/gen a hash
        },
        "dependencies": [c.alias() for c in config.components],
    }

    # TODO: send repository as file upload
    response = requests.post(f"{server_url}/policies/{policy_id}/versions", json=body)
    assert (
        response.status_code == 200
    ), f"Failed to create policy version: {response.content}"

    logging.debug(response.json())
    return response.json()["policy_version_id"]


def create_component(
    server_url: str,
    name: str,
    version: str,
    input_schema: str,
    output_schema: str,
    repository: str,
):
    if not os.path.exists(repository):
        raise FileNotFoundError(f"Path does not exist: {repository}")
    if not os.path.isdir(repository):
        raise ValueError(f"Path is not a directory: {repository}")

    response = requests.post(f"{server_url}/components", json={"name": name})
    component_id = response.json()["component_id"]

    component_info = ComponentVersionInfo(name, version, input_schema, output_schema)

    repository = pack_workspace(component_info.alias(), repository)
    logging.info(f"Creating component {name}")
    response = requests.post(
        f"{server_url}/components/{component_id}/versions",
        json={
            "alias": component_info.alias(),
            "input_schema": input_schema,
            "output_schema": output_schema,
            "repository": base64.b64encode(repository).decode("ascii"),
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create component version: {response.content}"

    return response.json()


def register_active_version(server_url, policy_id, policy_version_id):
    response = requests.put(
        f"{server_url}/policies/{policy_id}",
        json={"active_policy_version_id": policy_version_id},
    )
    assert response.status_code == 200, "Failed to activate policy version"


def update_workspace():
    pass


def delete_workspace():
    pass
