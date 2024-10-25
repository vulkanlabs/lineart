import os

import click
import requests

from vulkan_public.cli.auth import TOKEN_PATH, ensure_write, retrieve_credentials
from vulkan_public.cli.context import LoginContext, pass_login_context


@click.command()
@pass_login_context
def login(ctx: LoginContext):
    # 1. Check if there's an active session
    if os.path.exists(TOKEN_PATH):
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
            ensure_write(TOKEN_PATH, creds)
            ctx.logger.info("You are already signed in.")
            return
        else:
            ctx.logger.debug(f"Existing session is invalid: {response.content}")

    # 2. Base case: username and password are provided
    _base_login(ctx)


def _base_login(ctx: LoginContext):
    username = click.prompt("Your Vulkan username")
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
    ensure_write(TOKEN_PATH, data)
    ctx.logger.info("Sign-in successful.")
