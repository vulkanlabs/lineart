import json

import click

from vulkan.cli import client
from vulkan.cli.context import Context, pass_context
from vulkan.cli.exceptions import log_exceptions


@click.group()
def policy():
    pass


@policy.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--description", type=str, default="", help="Description of the policy")
def create(ctx: Context, name: str, description: str):
    return client.policy.create_policy(
        ctx,
        name,
        description,
        input_schema="{}",
        output_schema="",
    )


@policy.command()
@pass_context
@click.option("--policy_id", type=str)
@click.option("--policy_version_id", type=str)
def set_active_version(ctx: Context, policy_id: str, policy_version_id: str):
    return client.policy.set_active_version(ctx, policy_id, policy_version_id)


@policy.command()
@pass_context
@click.option("--policy_id", type=str)
@log_exceptions
def delete(ctx, policy_id: str):
    click.confirm(f"Are you sure you want to delete policy {policy_id}?", abort=True)
    ctx.logger.info(f"Deleting policy {policy_id}")
    return client.policy.delete_policy(ctx, policy_id)


@policy.command()
@pass_context
@click.option("--policy_id", type=str)
@click.option("--data", type=str)
@click.option("--timeout", type=int, default=15)
@log_exceptions
def trigger_run(ctx: Context, policy_id: str, data: str, timeout: int):
    # Call the function to trigger the Dagster job
    try:
        input_data = json.loads(data)
    except TypeError as e:
        raise ValueError(f"Invalid JSON data provided: {data}\nError: {e}")

    try:
        run_id, success = client.run.trigger_run_by_policy_id(
            ctx=ctx,
            policy_id=policy_id,
            input_data=input_data,
            timeout=timeout,
            time_step=5,
        )
        ctx.logger.info(
            f"Run {run_id} {'completed successfully' if success else 'failed'}"
        )
    except Exception as e:
        raise ValueError(f"Error triggering run: {e}")


@policy.command()
@pass_context
@click.option("--policy_id", type=str, required=True, help="Id of the policy")
@click.option(
    "--version_name", type=str, required=True, help="Name of the policy version"
)
@click.option("--repository_path", type=str, required=True, help="Path to repository")
@log_exceptions
def create_version(
    ctx: Context,
    policy_id: str,
    version_name: str,
    repository_path: str,
):
    return client.policy.create_policy_version(
        ctx, policy_id, version_name, repository_path
    )


@policy.command()
@pass_context
@click.option(
    "--policy_version_id",
    type=str,
    required=True,
    help="ID of the policy version",
)
@log_exceptions
def delete_version(
    ctx,
    policy_version_id: str,
):
    click.confirm(
        f"Are you sure you want to delete policy version {policy_version_id}?",
        abort=True,
    )
    ctx.logger.info(f"Deleting policy version {policy_version_id}")
    return client.policy.delete_policy_version(ctx, policy_version_id)
