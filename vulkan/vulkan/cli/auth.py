import json
import os

from vulkan.cli.logger import init_logger

TOKEN_PATH = os.path.expanduser("~/.config/vulkan/user.json")


logger = init_logger(__name__)


def retrieve_credentials():
    if not os.path.exists(TOKEN_PATH):
        raise FileNotFoundError(f"Credentials path not found: {TOKEN_PATH}")

    with open(TOKEN_PATH, "r") as fp:
        creds = json.load(fp)

    return {
        "x-stack-access-token": creds["access_token"],
        "x-stack-refresh-token": creds["refresh_token"],
    }


def ensure_write(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        logger.debug(f"Writing token to {path}")
        json.dump(data, f)
