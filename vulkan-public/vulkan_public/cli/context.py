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

        # TODO: This should handled by a Vulkan public API.
        # That way we abstract the auth provider away.
        self.stack_client_key = os.getenv(
            "STACK_PUBLISHABLE_CLIENT_KEY",
            "pck_cw8v2eeb9ke3de0amj9vrm6x8bzj7vr32hrbqywrspre8",
        )
        self.stack_project_id = os.getenv(
            "STACK_PROJECT_ID", "a80771c2-8a92-47c1-98ad-df4f06952640"
        )
        if self.stack_client_key is None or self.stack_project_id is None:
            msg = (
                "STACK_PUBLISHABLE_CLIENT_KEY and STACK_PROJECT_ID "
                "environment variables are required for Vulkan authentication"
            )
            self.logger.fatal(msg)
            raise click.Abort()


class Context:
    def __init__(self):
        self.logger = init_logger(__name__)
        self.server_url = os.getenv("VULKAN_SERVER_URL", "http://34.42.163.92:6001")
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
                "x-stack-access-token": creds["access_token"],
                "x-stack-refresh-token": creds["refresh_token"],
            }
        )


class CliContext(Context):
    def __init__(self):
        super().__init__()
        ctx = click.get_current_context()
        self.verbose = ctx.obj.get("verbose", False)


pass_context = click.make_pass_decorator(CliContext, ensure=True)
pass_login_context = click.make_pass_decorator(LoginContext, ensure=True)
