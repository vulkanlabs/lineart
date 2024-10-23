import click
from tabulate import tabulate

from vulkan_public.cli import client
from vulkan_public.cli.context import Context, pass_context
from vulkan_public.cli.exceptions import log_exceptions


@click.group()
def component():
    pass


@component.command()
@pass_context
@click.option("--all", is_flag=True, default=False, help="Include archived components")
@log_exceptions
def list(ctx: Context, all: bool):
    data = client.component.list_components(ctx, all)
    keys = ["component_id", "name", "archived", "created_at"]
    summary = [dict([(k, d[k]) for k in keys]) for d in data]
    tab = tabulate(summary, headers="keys", tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")


@component.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the component")
@log_exceptions
def create(
    ctx: Context,
    name: str,
):
    return client.component.create_component(ctx, name)


@component.command()
@pass_context
@click.argument("component_id", type=str, required=True)
@log_exceptions
def delete(
    ctx: Context,
    component_id: str,
):
    click.confirm(
        f"Are you sure you want to delete component {component_id}?", abort=True
    )
    ctx.logger.info(f"Deleting component {component_id}")
    return client.component.delete_component(ctx, component_id)


@component.command()
@pass_context
@click.argument("component_id", type=str, required=True)
@click.option(
    "--all", is_flag=True, default=False, help="Include archived component versions"
)
@log_exceptions
def list_versions(
    ctx: Context,
    component_id: str,
    all: bool,
):
    data = client.component.list_component_versions(ctx, component_id, all)
    keys = ["component_id", "component_version_id", "alias", "archived", "created_at"]
    summary = [dict([(k, d[k]) for k in keys]) for d in data]
    tab = tabulate(summary, headers="keys", tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")


@component.command()
@pass_context
@click.option("--component_id", type=str, required=True, help="ID of the component")
@click.option(
    "--version_name",
    type=str,
    required=True,
    help="Alias for the version of the component",
)
@click.option("--repository_path", type=str, required=True, help="Path to repository")
@log_exceptions
def create_version(
    ctx: Context,
    component_id: str,
    version_name: str,
    repository_path: str,
):
    return client.component.create_component_version(
        ctx, component_id, version_name, repository_path
    )


@component.command()
@pass_context
@click.argument("component_version_id", type=str, required=True)
@log_exceptions
def delete_version(
    ctx: Context,
    component_version_id: str,
):
    click.confirm(
        f"Are you sure you want to delete component version {component_version_id}?",
        abort=True,
    )
    ctx.logger.info(f"Deleting component version {component_version_id}")
    return client.component.delete_component_version(ctx, component_version_id)
