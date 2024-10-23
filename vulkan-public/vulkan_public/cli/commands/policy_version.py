import json

import click

from vulkan_public.cli import client
from vulkan_public.cli.context import Context, pass_context
from vulkan_public.cli.exceptions import log_exceptions


@click.group()
def policy_version():
    pass


@policy_version.command()
@pass_context
@click.option("--policy_version_id", type=str, required=True)
@click.option("--data", type=str, required=True)
@click.option("--config_variables", type=str, required=False)
@click.option("--timeout", type=int, default=15)
@log_exceptions
def trigger_run(
    ctx: Context,
    policy_version_id: str,
    data: str,
    config_variables: str | None,
    timeout: int,
):
    # Call the function to trigger the Dagster job
    try:
        input_data = json.loads(data)
    except TypeError as e:
        raise ValueError(f"Invalid JSON data provided: {data}\nError: {e}")

    if config_variables is not None:
        config_variables = json.loads(config_variables)

    try:
        run_id, success = client.run.trigger_run_by_policy_version_id(
            ctx=ctx,
            policy_version_id=policy_version_id,
            input_data=input_data,
            config_variables=config_variables,
            timeout=timeout,
            time_step=5,
        )
        ctx.logger.info(
            f"Run {run_id} {'completed successfully' if success else 'failed'}"
        )
    except Exception as e:
        raise ValueError(f"Error triggering run: {e}")


@policy_version.command()
@pass_context
@click.option("--policy_version_id", type=str, required=True)
@log_exceptions
def show_graph(ctx: Context, policy_version_id: str):
    response = client.policy.get_policy_version_graph(ctx, policy_version_id)
    click.echo(json.dumps(json.loads(response), indent=2))


@policy_version.command()
@pass_context
@click.option("--policy_version_id", type=str, required=True)
@click.argument("variables", type=str, required=True)
@log_exceptions
def set_variables(ctx: Context, policy_version_id: str, variables: str):
    variables = json.loads(variables)
    response = client.policy_version.set_variables(ctx, policy_version_id, variables)
    click.echo(json.dumps(response, indent=2))


@policy_version.command()
@pass_context
@click.option("--policy_version_id", type=str, required=True)
@log_exceptions
def list_variables(ctx: Context, policy_version_id: str):
    response = client.policy_version.list_variables(ctx, policy_version_id)
    click.echo(json.dumps(response, indent=2))
