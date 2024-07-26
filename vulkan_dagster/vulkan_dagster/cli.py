import logging
import os
from argparse import ArgumentParser
from io import BytesIO
from shutil import make_archive
from zipfile import ZipFile

import requests

logging.basicConfig(level=logging.INFO)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser("create_workspace", help="Create a workspace")
    create.add_argument("--name", type=str, required=True, help="Name of the workspace")
    create.add_argument(
        "--repository", type=str, required=True, help="Path to repository"
    )
    create.add_argument("--path", type=str, required=True, help="Path to workspace")
    args = parser.parse_args()

    if args.command == "create_workspace":
        create_workspace(args.name, args.repository, args.path)
    else:
        raise ValueError(f"Unknown command: {args.command}")


def config_environment():
    # TODO: create the config as a yaml file dynamically
    # so it can later be used to create / update the workspace.
    pass


TEMP_DIR = "./.tmp"


# TODO: at the moment we assume repository is a path in local disk,
# but this could be a remote repository in git etc
def create_workspace(
    name: str,
    description: str,
    input_schema: str,
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

    os.makedirs(TEMP_DIR, exist_ok=True)
    basename = f"{TEMP_DIR}/{name}"
    filename = make_archive(basename, "gztar", repository)
    with open(filename, "rb") as f:
        try:
            logging.info(f"Creating workspace {name}: from {repository} at {path}")

            response = requests.post(
                "http://localhost:6000/policies/create",
                data={
                    "name": name,
                    "description": description,
                    "input_schema": input_schema,
                    "workspace": path,
                    "job_name": "policy",
                },
                files={"workspace": f},
            )
            if response.status_code != 200:
                logging.error(f"Failed to create policy: {response.text}")
                raise Exception(f"Failed to create policy: {response.text}")

        except Exception as e:
            logging.error(f"Failed to create workspace: {e}")
            f.close()
            os.remove(filename)


def update_workspace():
    pass


def delete_workspace():
    pass
