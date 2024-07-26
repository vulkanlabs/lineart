from argparse import ArgumentParser
from io import BytesIO
from zipfile import ZipFile

import logging
import os

import requests

logging.basicConfig(level=logging.INFO)


def main():
    parser = ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    create = subparsers.add_parser(
        "create_workspace", help="Create a workspace"
    )
    create.add_argument(
        "--path", type=str, required=True, help="Path to workspace"
    )

    args = parser.parse_args()

    if args.command == "create_workspace":
        create_workspace(args.path)
    else:
        raise ValueError(f"Unknown command: {args.command}")


def config_environment():
    pass


def create_workspace(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Path does not exist: {path}")

    if os.path.isdir(path):
        buffer = BytesIO()
        with ZipFile(buffer, "w") as zip_ref:
            for root, _, files in os.walk(path):
                for file in files:
                    zip_ref.write(os.path.join(root, file), file)
        file = buffer.getvalue()
        mode = "python_module"
    else:
        file = open(path, "r")
        mode = "python_file"

    logging.info(f"Creating workspace: {path}")
    response = requests.post(
        "http://localhost:3001/workspace/create",
        data={"name": os.path.basename(path), "mode": mode},
        files={"workspace": file},
    )
    if response.status_code != 200:
        raise Exception(f"Failed to create workspace: {response.text}")
    logging.info("Workspace created")


def update_workspace():
    pass


def delete_workspace():
    pass
