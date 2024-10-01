import json

import click

from vulkan.cli import client
from vulkan.cli.context import Context, pass_context
from vulkan.cli.exceptions import log_exceptions


@click.group()
def run():
    pass


@run.command()
@click.argument("run_id")
@pass_context
@log_exceptions
def data(ctx: Context, run_id: str):
    response = client.run.get_run_data(ctx, run_id)
    click.echo(json.dumps(response, indent=2))
