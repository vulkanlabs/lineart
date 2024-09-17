import os

import click

from vulkan.cli.logger import init_logger
from vulkan.cli.session import init_session


class Context:
    def __init__(self):
        self.server_url = os.getenv(
            "VULKAN_SERVER_URL",
            "http://localhost:6001",
        )

        self.logger = init_logger(__name__)
        self.session = init_session()


pass_context = click.make_pass_decorator(Context, ensure=True)
