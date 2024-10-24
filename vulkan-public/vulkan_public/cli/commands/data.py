import json

import click
from tabulate import tabulate

from vulkan_public.cli import client
from vulkan_public.cli.context import Context, pass_context
from vulkan_public.cli.exceptions import log_exceptions


@click.group()
def data():
    pass


@data.command()
@pass_context
@click.option(
    "--all", "-a", is_flag=True, default=False, help="Include archived data sources"
)
@log_exceptions
def list_sources(ctx: Context, all: bool):
    data = client.data.list_data_sources(ctx, all)
    keys = ["data_source_id", "name", "archived", "created_at", "last_updated_at"]
    summary = [dict([(k, d[k]) for k in keys]) for d in data]
    tab = tabulate(summary, headers="keys", tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")


@data.command()
@pass_context
@click.option(
    "--config_path", type=str, required=True, help="Path to the data source config file"
)
@log_exceptions
def create_source(
    ctx: Context,
    config_path: str,
):
    return client.data.create_data_source(ctx, config_path)


@data.command()
@pass_context
@click.argument("data_source_id", type=str, required=True)
@log_exceptions
def get_source(
    ctx: Context,
    data_source_id: str,
):
    data_source = client.data.get_data_source(ctx, data_source_id)
    click.echo(json.dumps(data_source, indent=4))


@data.command()
@pass_context
@click.argument("data_source_id", type=str, required=True)
@log_exceptions
def delete_source(
    ctx: Context,
    data_source_id: str,
):
    click.confirm(
        f"Are you sure you want to delete data source {data_source_id}?", abort=True
    )
    ctx.logger.info(f"Deleting data source {data_source_id}")
    return client.data.delete_data_source(ctx, data_source_id)


@data.command()
@pass_context
@click.argument("data_source_id", type=str, required=True)
@log_exceptions
def list_objects(
    ctx: Context,
    data_source_id: str,
):
    data = client.data.list_data_objects(ctx, data_source_id)
    keys = ["data_source_id", "data_object_id", "key", "created_at"]
    summary = [dict([(k, d[k]) for k in keys]) for d in data]
    tab = tabulate(summary, headers="keys", tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")
