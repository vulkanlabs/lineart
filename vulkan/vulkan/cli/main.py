import click

from vulkan.cli import commands
from vulkan.cli.logger import init_logger

logger = init_logger(__name__)


@click.group()
def cli():
    pass


cli.add_command(commands.login.login)
cli.add_command(commands.component.component)
cli.add_command(commands.policy.policy)
cli.add_command(commands.run.run)


def config_environment():
    # TODO: create the config as a yaml file dynamically
    # so it can later be used to create / update the workspace.
    pass
