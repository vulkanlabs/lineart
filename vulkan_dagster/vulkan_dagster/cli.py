import base64
import logging
import os
from argparse import ArgumentParser

import requests

from .workspace import pack_workspace

logging.basicConfig(level=logging.DEBUG)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    workspace = subparsers.add_parser("create_workspace", help="Create a workspace")
    workspace.add_argument("--name", type=str, required=True, help="Name of the workspace")
    workspace.add_argument(
        "--repository", type=str, required=True, help="Path to repository"
    )
    workspace.add_argument("--path", type=str, required=True, help="Path to workspace")

    component = subparsers.add_parser("create_component", help="Create a component")
    component.add_argument("--name", type=str, required=True, help="Name of the component")
    component.add_argument(
        "--repository", type=str, required=True, help="Path to repository"
    )

    args = parser.parse_args()

    SERVER_URL = "http://localhost:6000"
    if args.command == "create_workspace":
        policy_id = create_policy(SERVER_URL, args.name, "", "")
        logging.info(f"Created policy {policy_id}")
        policy_version_id = create_policy_version(
            SERVER_URL, policy_id, args.name, args.repository, args.path
        )
        logging.info(
            f"Created workspace {args.name} with policy version {policy_version_id}"
        )
        register_active_version(SERVER_URL, policy_id, policy_version_id)

    elif args.command == "create_component":
        create_component(SERVER_URL, args.name, args.repository)
        logging.info(
            f"Created component {args.name}"
        )

    else:
        raise ValueError(f"Unknown command: {args.command}")


def config_environment():
    # TODO: create the config as a yaml file dynamically
    # so it can later be used to create / update the workspace.
    pass


def create_policy(server_url, name, description, input_schema):
    response = requests.post(
        f"{server_url}/policies/create",
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
    repository,
    path,
):
    if not os.path.exists(repository):
        raise FileNotFoundError(f"Path does not exist: {repository}")
    if not os.path.isdir(repository):
        raise ValueError(f"Path is not a directory: {repository}")

    expanded_path = os.path.join(repository, path)
    if not os.path.exists(expanded_path):
        msg = f"Path does not exist: {path} - resolved to: {expanded_path}"
        raise FileNotFoundError(msg)
    if not os.path.isdir(expanded_path):
        msg = f"Path is not a directory: {path} - resolved to: {expanded_path}"
        raise ValueError(msg)

    repository = pack_workspace(name, repository)
    logging.info(f"Creating workspace {name} at {path}")
    # TODO: send repository as file upload
    response = requests.post(
        f"{server_url}/policies/{policy_id}/versions/create",
        json={
            "policy_id": policy_id,
            "alias": name,
            "repository": base64.b64encode(repository).decode("ascii"),
            "repository_version": "0.0.1",
            "entrypoint": path,
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create policy version: {response.content}"

    logging.debug(response.json())
    return response.json()["policy_version_id"]


def create_component(
    server_url: str,
    name: str,
    repository,
):
    if not os.path.exists(repository):
        raise FileNotFoundError(f"Path does not exist: {repository}")
    if not os.path.isdir(repository):
        raise ValueError(f"Path is not a directory: {repository}")

    repository = pack_workspace(name, repository)
    logging.info(f"Creating component {name}")
    response = requests.post(
        f"{server_url}/components/create",
        data={
            "name": name,
            "repository": base64.b64encode(repository),
        },
    )
    assert (
        response.status_code == 200
    ), f"Failed to create component version: {response.content}"

    return response.json()


def register_active_version(server_url, policy_id, policy_version_id):
    response = requests.put(
        f"{server_url}/policies/{policy_id}/update",
        json={"active_policy_version_id": policy_version_id},
    )
    assert response.status_code == 200, "Failed to activate policy version"


def update_workspace():
    pass


def delete_workspace():
    pass
