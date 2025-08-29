import click

from lineart.auth.command_login import login
from lineart.logging import init_logger
from lineart.projects.command_projects import projects

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


cli.add_command(login)
cli.add_command(projects, name="projects")
