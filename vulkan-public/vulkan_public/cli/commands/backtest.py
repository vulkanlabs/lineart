import click

from vulkan_public.cli import client as vulkan
from vulkan_public.cli.context import Context, pass_context
from vulkan_public.cli.exceptions import log_exceptions


@click.group()
def backtest():
    pass


@backtest.command()
@pass_context
@log_exceptions
def list(ctx: Context):
    data = vulkan.backtest.list_backtests(ctx)
    print(data)


@backtest.command()
@click.option("--policy_version_id", type=str, required=True)
@click.option("--file_format", type=str, required=True)
@click.argument("input_file_path", type=str, required=True)
@pass_context
@log_exceptions
def create(
    ctx: Context,
    policy_version_id: str,
    input_file_path: str,
    file_format: str,
):
    results = vulkan.backtest.create_backtest(
        ctx, policy_version_id, input_file_path, file_format
    )
    print(results)
