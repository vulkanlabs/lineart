import click
from rich.console import Console
from rich.table import Table

# Assuming these imports exist from your project structure
from lineart.auth.login import LoginContext, pass_login_context
from lineart.client import Lineart


@click.group()
def projects():
    """Manage projects."""
    pass


@click.command("list", help="List all projects")
@pass_login_context
def list_projects(ctx: LoginContext):
    """List all projects available to the user."""
    lineart = Lineart()
    current_project_id = lineart._get_project_id()
    try:
        projects_list = _list_projects(lineart)
        _display_projects(current_project_id, projects_list)
    except RuntimeError as e:
        ctx.logger.error(f"Error listing projects: {e}")
        raise click.Abort()


@click.command("set", help="Set the active project by ID.")
@click.argument("project_id", required=False, type=str)
@pass_login_context
def set_project(ctx: LoginContext, project_id: str | None):
    """
    Sets the VULKAN_PROJECT_ID in the config file.

    If a PROJECT_ID is provided, it sets it directly after validation.
    If no PROJECT_ID is provided, it lists available projects and prompts for a selection.
    """
    lineart = Lineart()
    console = Console()
    try:
        projects_list = _list_projects(lineart)
        # Create a dictionary for quick lookups
        project_map = {p["project_id"]: p for p in projects_list}
    except RuntimeError as e:
        ctx.logger.error(f"Could not fetch projects: {e}")
        raise click.Abort()

    if not projects_list:
        console.print("[yellow]No projects available to set.[/yellow]")
        return

    selected_project_id = None
    current_project_id = lineart._get_project_id()

    if project_id:
        # Mode 1: Project ID is passed as an argument
        if project_id in project_map:
            selected_project_id = project_id
        else:
            console.print(
                f"[red]Error:[/red] Project with ID '{project_id}' not found."
            )
            _display_projects(current_project_id, projects_list)
            raise click.Abort()
    else:
        # Mode 2: Interactive selection
        _display_projects(current_project_id, projects_list)

        choice_str = click.prompt("Select a project by number", type=str)
        try:
            choice_idx = int(choice_str) - 1
            if 0 <= choice_idx < len(projects_list):
                selected_project_id = projects_list[choice_idx]["project_id"]
            else:
                raise ValueError  # Choice is out of bounds
        except (ValueError, IndexError):
            console.print(
                f"[red]Error:[/red] Invalid selection. Please enter a number from 1 to {len(projects_list)}."
            )
            raise click.Abort()

    if selected_project_id:
        lineart._save_project_id(selected_project_id)
        project_name = project_map[selected_project_id]["name"]
        console.print(
            f"[green]✅ Success![/green] Active project set to '{project_name}' ({selected_project_id})."
        )


# Add the new commands to the 'projects' group
projects.add_command(list_projects)
projects.add_command(set_project)


def _list_projects(lineart: Lineart) -> list[dict]:
    """Handles the API call to fetch projects."""
    # Remove any existing /projects suffix. gambiarra to avoid conflict in platform setup.
    base_url = lineart.server_url.split("/projects")[0]
    url = base_url + "/projects"
    resp = lineart.sdk_configuration.client.request(method="GET", url=url)

    if resp.status_code != 200:
        raise RuntimeError(
            f"Failed to list projects: {resp.status_code} {resp.content}"
        )
    return resp.json()


def _display_projects(current_project_id: str | None, projects: list[dict]):
    """Helper function to display projects in a rich table."""
    if not projects:
        Console().print("[yellow]No projects found.[/yellow]")
        return

    table = Table(title="Available Projects")
    table.add_column("#", style="magenta", justify="right")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="white", no_wrap=True)
    table.add_column("Selected", style="green", no_wrap=True)

    for i, project in enumerate(projects, start=1):
        is_selected = "✅" if project["project_id"] == current_project_id else ""
        row_data = [
            str(i),
            project["project_id"],
            project["name"],
            is_selected,
        ]
        table.add_row(*row_data)

    Console().print(table)
