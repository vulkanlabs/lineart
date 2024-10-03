import click

from vulkan_public.cli import client
from vulkan_public.cli.context import Context, pass_context
from vulkan_public.cli.exceptions import log_exceptions


@click.group()
def component():
    pass


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
@click.option("--component_id", type=str, required=True, help="ID of the component")
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
@click.option("--component_id", type=str, required=True, help="ID of the component")
@click.option(
    "--component_version_id",
    type=str,
    required=True,
    help="ID of the component version",
)
@log_exceptions
def delete_version(
    ctx: Context,
    component_id: str,
    component_version_id: str,
):
    click.confirm(
        f"Are you sure you want to delete component version {component_version_id}?",
        abort=True,
    )
    ctx.logger.info(f"Deleting component version {component_version_id}")
    return client.component.delete_component_version(
        ctx, component_id, component_version_id
    )
