import click
from tabulate import tabulate

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
    display_keys = [
        "backtest_id",
        "policy_version_id",
        "status",
        "created_at",
        "last_updated_at",
    ]

    data = vulkan.backtest.list_backtests(ctx)
    tab_data = [{k: v for k, v in d.items() if k in display_keys} for d in data]
    tab = tabulate(tab_data, headers="keys", tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")


@backtest.command()
@pass_context
@click.argument("backtest_id", type=str, required=True)
@log_exceptions
def get(ctx: Context, backtest_id: str):
    display_keys = [
        "backtest_id",
        "policy_version_id",
        "status",
        "created_at",
        "last_updated_at",
        "input_data_path",
        "results_path",
    ]
    data = vulkan.backtest.get_backtest(ctx, backtest_id)
    tab_data = {k: v for k, v in data.items() if k in display_keys}
    tab = tabulate(tab_data.items(), headers=display_keys, tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")


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
    display_keys = [
        "backtest_id",
        "policy_version_id",
        "status",
        "created_at",
        "last_updated_at",
        "input_data_path",
        "results_path",
    ]
    tab_data = {k: v for k, v in results.items() if k in display_keys}
    tab = tabulate(tab_data.items(), headers=display_keys, tablefmt="pretty")
    ctx.logger.info(f"\n{tab}")
