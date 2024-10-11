import click

from vulkan_public.cli import commands
from vulkan_public.cli.logger import init_logger

logger = init_logger(__name__)


@click.group()
@click.pass_context
@click.option(
    "--verbose",
    is_flag=True,
    default=False,
    help=(
        "When set, will raise any python exception that occurs "
        "instead of just logging the error message."
    ),
)
def cli(ctx: click.core.Context, verbose: bool):
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose


cli.add_command(commands.login.login)
cli.add_command(commands.component.component)
cli.add_command(commands.policy.policy)
cli.add_command(commands.policy_version.policy_version)
cli.add_command(commands.run.run)


def config_environment():
    # TODO: create the config as a yaml file dynamically
    # so it can later be used to create / update the workspace.
    pass
