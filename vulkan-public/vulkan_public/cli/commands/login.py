import click

from vulkan_public.cli.auth import base_login, refresh_credentials
from vulkan_public.cli.context import LoginContext, pass_login_context


@click.command()
@pass_login_context
def login(ctx: LoginContext):
    # 1. Check if there's an active session
    refresh_credentials(ctx)

    # 2. Base case: username and password are provided
    base_login(ctx)
