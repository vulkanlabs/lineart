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


class Context:
    def __init__(self):
        self.server_url = os.getenv(
            "VULKAN_SERVER_URL",
            "http://localhost:6001",
        )

        self.logger = init_logger(__name__)
        creds = retrieve_credentials()
        self.session = init_session(
            headers={
                "x-stack-access-token": creds["access_token"],
                "x-stack-refresh-token": creds["refresh_token"],
            }
        )


pass_context = click.make_pass_decorator(Context, ensure=True)
pass_login_context = click.make_pass_decorator(LoginContext, ensure=True)
