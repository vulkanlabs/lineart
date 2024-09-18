import click

from vulkan.cli import client
from vulkan.cli.context import Context, pass_context


@click.group()
def component():
    pass


@component.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the component")
def create(
    ctx: Context,
    name: str,
):
    return client.component.create_component(ctx, name)


@component.command()
@pass_context
@click.option("--component_id", type=str, required=True, help="ID of the component")
@click.option("--component_name", type=str, required=True, help="Name of the component")
@click.option(
    "--version", type=str, required=True, help="Alias for the version of the component"
)
@click.option("--repository_path", type=str, required=True, help="Path to repository")
def create_version(
    ctx: Context,
    component_id: str,
    component_name: str,
    version: str,
    repository_path: str,
):
    return client.component.create_component_version(
        ctx, component_id, component_name, version, repository_path
    )
