import click
from requests import ConnectionError

from lineart.auth.login import (
    LoginContext,
    base_login,
    pass_login_context,
    refresh_credentials,
)


@click.command()
@pass_login_context
def login(ctx: LoginContext):
    # 1. Check if there's an active session
    ok = refresh_credentials(ctx)
    if ok:
        ctx.logger.info("You are already signed in.")
        return

    # 2. Base case: username and password are provided
    try:
        base_login(ctx)
    except ConnectionError as e:
        ctx.logger.error(f"Failed to connect to auth server: {ctx.auth_server_url}")
        ctx.logger.debug(f"Error details: {e}")
        click.Abort()
