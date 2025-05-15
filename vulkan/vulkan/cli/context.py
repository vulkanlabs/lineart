import os

import click
from requests import Session

from vulkan.cli.logger import init_logger


class Context:
    def __init__(self, logging_level: str = "INFO"):
        self.logger = init_logger(__name__, logging_level)
        self.server_url = os.getenv("VULKAN_SERVER_URL", "http://34.132.4.82:6001")
        if self.server_url is None:
            self.logger.info("VULKAN_SERVER_URL environment variable is not set")
            raise click.Abort()

        self.session = Session()


class CliContext(Context):
    def __init__(self):
        super().__init__()
        ctx = click.get_current_context()
        self.verbose = ctx.obj.get("verbose", False)


pass_context = click.make_pass_decorator(CliContext, ensure=True)
