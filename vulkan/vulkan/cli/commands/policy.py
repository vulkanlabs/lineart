import json
import time

import click

from vulkan.cli import client
from vulkan.cli.context import Context, pass_context


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
@click.option("--data", type=str)
@click.option("--timeout", type=int, default=15)
def trigger_run(ctx: Context, policy_id: str, data: str, timeout: int):
    # Call the function to trigger the Dagster job
    execution_config = {
        "execution": {
            "config": {
                "multiprocess": {
                    "max_concurrent": 5,
                    "retries": {"disabled": {}},
                }
            }
        },
        "ops": {"input_node": {"config": json.loads(data)}},
    }

    response = ctx.session.post(
        f"{ctx.server_url}/policies/{policy_id}/runs",
        json={"execution_config_str": json.dumps(execution_config)},
    )
    ctx.logger.debug(response.json())

    # Get the run status
    run_id = response.json()["run_id"]
    response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}")
    ctx.logger.debug(response.json())

    success = False
    # Poll the API until the job is completed
    step_size = 3
    for _ in range(0, timeout, step_size):
        response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}")
        ctx.logger.debug(response.json())
        try:
            status = response.json()["status"]
            if status == "SUCCESS":
                success = True
                break
        except (KeyError, json.decoder.JSONDecodeError):
            continue
        time.sleep(step_size)

    assert success, f"Run {run_id} for policy {policy_id} did not complete successfully"


@policy.command()
@pass_context
@click.option("--policy_id", type=str, required=True, help="Id of the policy")
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--repository_path", type=str, required=True, help="Path to repository")
def create_version(
    ctx: Context,
    policy_id: str,
    name: str,
    repository_path: str,
):
    return client.policy.create_policy_version(ctx, policy_id, name, repository_path)
