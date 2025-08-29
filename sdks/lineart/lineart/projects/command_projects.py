import click
from rich.console import Console
from rich.table import Table

from lineart.auth.login import LoginContext, pass_login_context
from lineart.client import Lineart


def _list(lineart: Lineart) -> list[dict]:
    url = lineart.server_url + "/projects"
    resp = lineart.sdk_configuration.client.request(method="GET", url=url)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to list projects: {resp.status_code} {resp.content}"
        )
    projects = resp.json()
    return projects


@click.command("list", help="List all projects")
@pass_login_context
def list_projects(ctx: LoginContext):
    """List all projects available to the user."""
    lineart = Lineart()

    try:
        projects = _list(lineart)
    except RuntimeError as e:
        ctx.logger.error(f"Error listing projects: {e}")
        click.Abort()

    if not projects:
        ctx.logger.info("No projects found.")
        return

    table = Table(title="Projects")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white", no_wrap=True)

    for project in projects:
        table.add_row(project["project_id"], project["name"])

    console = Console()
    console.print(table)


@click.group
def projects():
    """Manage projects."""
    pass


projects.add_command(list_projects)
