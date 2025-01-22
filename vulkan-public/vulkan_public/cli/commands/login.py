import click

from vulkan_public.cli.auth import base_login, refresh_credentials
from vulkan_public.cli.context import LoginContext, pass_login_context


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
