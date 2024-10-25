import os

import click

from vulkan_public.cli.auth import retrieve_credentials
from vulkan_public.cli.logger import init_logger
from vulkan_public.cli.session import init_session


class LoginContext:
    """
    Context for login commands.

    Does not include the session object or try to load credentials.
    """

    def __init__(self):
        self.logger = init_logger(__name__)
        self.auth_server_url = os.getenv(
            "VULKAN_AUTH_URL",
            "https://engine.vulkan.software",
        )


class Context:
    def __init__(self):
        self.logger = init_logger(__name__)
        self.server_url = os.getenv("VULKAN_SERVER_URL", "http://34.132.4.82:6001")
        if self.server_url is None:
            self.logger.info("VULKAN_SERVER_URL environment variable is not set")
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
                "x-stack-access-token": creds["accessToken"],
                "x-stack-refresh-token": creds["refreshToken"],
            }
        )


class CliContext(Context):
    def __init__(self):
        super().__init__()
        ctx = click.get_current_context()
        self.verbose = ctx.obj.get("verbose", False)


pass_context = click.make_pass_decorator(CliContext, ensure=True)
pass_login_context = click.make_pass_decorator(LoginContext, ensure=True)
