import os

import click

from vulkan.cli.auth import retrieve_credentials
from vulkan.cli.logger import init_logger
from vulkan.cli.session import init_session


class LoginContext:
    """
    Context for login commands.

    Does not include the session object or try to load credentials.
    """

    def __init__(self):
        self.logger = init_logger(__name__)

        # TODO: This should handled by a Vulkan public API.
        # That way we abstract the auth provider away.
        self.stack_client_key = os.getenv("STACK_PUBLISHABLE_CLIENT_KEY")
        self.stack_project_id = os.getenv("STACK_PROJECT_ID")
        if self.stack_client_key is None or self.stack_project_id is None:
            msg = (
                "STACK_PUBLISHABLE_CLIENT_KEY and STACK_PROJECT_ID "
                "environment variables are required for Vulkan authentication"
            )
            self.logger.fatal(msg)
            raise click.Abort()


class Context:
    def __init__(self):
        ctx = click.get_current_context()
        self.verbose = ctx.obj.get("verbose", False)
        self.logger = init_logger(__name__)
        self.server_url = os.getenv("VULKAN_SERVER_URL")
        if self.server_url is None:
            self.logger("VULKAN_SERVER_URL environment variable is not set")
            raise click.Abort()

        try:
            creds = retrieve_credentials()
        except FileNotFoundError:
            self.logger.fatal(
                "No credentials found. Sign in with `vulkan login` and try again."
            )
            raise click.Abort()

        self.session = init_session(
            headers={
                "x-stack-access-token": creds["access_token"],
                "x-stack-refresh-token": creds["refresh_token"],
            }
        )


pass_context = click.make_pass_decorator(Context, ensure=True)
pass_login_context = click.make_pass_decorator(LoginContext, ensure=True)
