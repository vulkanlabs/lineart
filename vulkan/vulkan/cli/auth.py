import json
import os

import click
import requests

from vulkan.cli.logger import init_logger

TOKEN_PATH = os.path.expanduser("~/.config/vulkan/user.json")
# TODO: This should handled by a Vulkan public API.
# That way we abstract the auth provider away.
AUTH_SIGNIN_URL = os.get_env("AUTH_SIGNIN_URL")
STACK_PUBLISHABLE_CLIENT_KEY = os.get_env("STACK_PUBLISHABLE_CLIENT_KEY")
STACK_PROJECT_ID = os.get_env("STACK_PROJECT_ID")


logger = init_logger(__name__)


@click.command()
@click.option(
    "--username",
    prompt="Your Vulkan username",
    help="The email you use to sign in to Vulkan Engine.",
)
@click.password_option(
    "--password",
    prompt="Your Vulkan password",
    help="The password you use to sign in to Vulkan Engine.",
    confirmation_prompt=False,
)
def login(username, password):
    # 1. Checa se já tem um token ativo
    # 2. Se não, checa se tem um refresh token
    # 3. Se não, checa se tem um username salvo
    # 4. Se não, pede o username e senha

    # Base case: username and password are provided
    response = requests.post(
        AUTH_SIGNIN_URL,
        json={"email": username, "password": password},
        # TODO: move to internal vulkan API
        headers={
            "x-stack-publishable-client-key": STACK_PUBLISHABLE_CLIENT_KEY,
            "x-stack-project-id": STACK_PROJECT_ID,
            "x-stack-access-type": "client",
        },
    )
    assert response.status_code == 200, f"Failed to sign in: {response.content}"
    data = response.json()
    _ensure_write(TOKEN_PATH, data)


def _ensure_write(path: str, data: dict):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        logger.debug(f"Writing token to {path}")
        json.dump(data, f)


if __name__ == "__main__":
    login()
