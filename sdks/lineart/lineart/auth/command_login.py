import click

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
    base_login(ctx)
