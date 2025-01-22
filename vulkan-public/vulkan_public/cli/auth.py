import json
import os

import click
import requests

from vulkan_public.cli.logger import init_logger

logger = init_logger(__name__)


class LoginContext:
    """
    Context for login commands.

    Does not include the session object or try to load credentials.
    """

    def __init__(self, log_level: str = "INFO"):
        self.logger = init_logger(__name__, log_level)
        self.auth_server_url = os.getenv(
            "VULKAN_AUTH_URL",
            "https://engine.vulkan.software",
        )


def refresh_credentials(ctx: LoginContext) -> bool:
    if not os.path.exists(_TOKEN_PATH):
        return False

    ctx.logger.info("Checking for existing session...")
    current_creds = retrieve_credentials()
    response = requests.get(
        f"{ctx.auth_server_url}/auth/sessions/current",
        headers={
            "x-stack-access-token": current_creds["accessToken"],
            "x-stack-refresh-token": current_creds["refreshToken"],
        },
    )
    if response.status_code == 200:
        creds = current_creds.copy()
        data = response.json()
        creds.update(data)
        _ensure_write(_TOKEN_PATH, creds)
        ctx.logger.info("You are already signed in.")
        return True

    ctx.logger.debug(f"Existing session is invalid: {response.content}")
    return False


def base_login(ctx: LoginContext):
    username = click.prompt("Your email address", show_default=True)
    password = click.prompt(
        "Your Vulkan password",
        hide_input=True,
        confirmation_prompt=False,
        show_default=False,
    )
    response = requests.post(
        f"{ctx.auth_server_url}/auth/sessions/new",
        json={"email": username, "password": password},
    )
    if response.status_code != 200:
        ctx.logger.error(
            f"Failed to sign in: status {response.status_code} \n"
            + f"{response.content}"
        )
        return
    data = response.json()
    _ensure_write(_TOKEN_PATH, data)
    ctx.logger.info("Sign-in successful.")


def retrieve_credentials():
    if not os.path.exists(_TOKEN_PATH):
        raise FileNotFoundError(f"Credentials path not found: {_TOKEN_PATH}")

    with open(_TOKEN_PATH, "r") as fp:
        creds = json.load(fp)

    return creds


_TOKEN_PATH = os.path.expanduser("~/.config/vulkan/user.json")


def _ensure_write(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        logger.debug(f"Writing token to {path}")
        json.dump(data, f)
