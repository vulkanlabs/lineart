import base64
import logging
import os
from argparse import ArgumentParser

import requests
import yaml

from .workspace import pack_workspace

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
    workspace.add_argument(
        "--entrypoint", type=str, required=True, help="Entrypoint to Vulkan module"
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
            SERVER_URL, policy_id, args.name, args.repository_path, args.entrypoint
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
    name: str,
    repository_path: str,
    entrypoint: str,
):
    if not os.path.exists(repository_path):
        raise FileNotFoundError(f"Path does not exist: {repository_path}")
    if not os.path.isdir(repository_path):
        raise ValueError(f"Path is not a directory: {repository_path}")

    expanded_path = os.path.join(repository_path, entrypoint)
    if not os.path.exists(expanded_path):
        msg = f"Path does not exist: {entrypoint} - resolved to: {expanded_path}"
        raise FileNotFoundError(msg)
    if not os.path.isdir(expanded_path):
        msg = f"Path is not a directory: {entrypoint} - resolved to: {expanded_path}"
        raise ValueError(msg)

    repository = pack_workspace(name, repository_path)
    logging.info(f"Creating workspace {name} at {entrypoint}")

    body = {
        "config": {
            "policy_id": policy_id,
            "alias": name,
            "repository": base64.b64encode(repository).decode("ascii"),
            "repository_version": "0.0.1",
            "entrypoint": entrypoint,
        },
    }

    # TODO: should config be mandatory? or just another way to pass cli params?
    config_path = os.path.join(expanded_path, "vulkan.yaml")
    if os.path.exists(config_path):
        # TODO: validate schema config
        # config = VulkanWorkspaceConfig.from_dict(config_data)
        with open(config_path, "r") as fn:
            config = yaml.safe_load(fn)
        if "components" in config.keys():
            body["dependencies"] = [
                _make_component_alias(c["name"], c["version"])
                for c in config["components"]
            ]

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

    alias = _make_component_alias(name, version)
    repository = pack_workspace(alias, repository)
    logging.info(f"Creating component {name}")
    response = requests.post(
        f"{server_url}/components/{component_id}/versions",
        json={
            "alias": alias,
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


def _make_component_alias(name: str, version: str):
    return f"{name}:{version}"
