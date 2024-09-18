import os

import click
import requests

from vulkan.cli.auth import TOKEN_PATH, ensure_write, retrieve_credentials
from vulkan.cli.context import LoginContext, pass_login_context

# TODO: This should handled by a Vulkan public API.
# That way we abstract the auth provider away.
STACK_PUBLISHABLE_CLIENT_KEY = os.getenv("STACK_PUBLISHABLE_CLIENT_KEY")
STACK_PROJECT_ID = os.getenv("STACK_PROJECT_ID")


@click.command()
@pass_login_context
def login(ctx: LoginContext):
    default_headers = {
        "x-stack-publishable-client-key": STACK_PUBLISHABLE_CLIENT_KEY,
        "x-stack-project-id": STACK_PROJECT_ID,
        "x-stack-access-type": "client",
    }
    if os.path.exists(TOKEN_PATH):
        ctx.logger.info("Checking for existing session...")
        current_creds = retrieve_credentials()
        # 1. Check if there's an active session
        headers = default_headers.copy()
        headers.update(
            {
                "x-stack-access-token": current_creds["access_token"],
                "x-stack-refresh-token": current_creds["refresh_token"],
            }
        )
        response = requests.get(
            "https://api.stack-auth.com/api/v1/users/me",
            headers=headers,
        )
        if response.status_code == 200:
            ctx.logger.info("You are already signed in.")
            return
        else:
            ctx.logger.debug(f"Existing session is invalid: {response.content}")

        # 2. Check if the refresh token is still valid
        headers = default_headers.copy()
        headers.update(
            {
                "x-stack-refresh-token": current_creds["refresh_token"],
            }
        )
        response = requests.post(
            "https://api.stack-auth.com/api/v1/auth/sessions/current/refresh",
            headers=headers,
        )
        if response.status_code == 200:
            # The response contains only the new access token.
            creds = current_creds.copy()
            data = response.json()
            creds.update(data)
            ensure_write(TOKEN_PATH, creds)
            ctx.logger.debug("Refreshed session from existing token.")
            ctx.logger.info("You are already signed in.")
            return
        else:
            ctx.logger.debug("Failed to refresh session. Signing in again.")
            ctx.logger.debug(f"Response: {response.content}")

    # 3. Base case: username and password are provided
    _base_login(ctx, headers=default_headers)


def _base_login(ctx: LoginContext, headers: dict):
    username = click.prompt("Your Vulkan username")
    password = click.prompt(
        "Your Vulkan password",
        hide_input=True,
        confirmation_prompt=False,
        show_default=False,
    )
    response = requests.post(
        "https://api.stack-auth.com/api/v1/auth/password/sign-in",
        json={"email": username, "password": password},
        # TODO: move to internal vulkan API
        headers=headers,
    )
    if response.status_code != 200:
        ctx.logger.error(
            f"Failed to sign in: status {response.status_code} \n"
            + f"{response.content}"
        )
        raise ValueError(f"Failed to sign in: {response.content}")
    data = response.json()
    ensure_write(TOKEN_PATH, data)
    ctx.logger.info("You are now signed in.")
