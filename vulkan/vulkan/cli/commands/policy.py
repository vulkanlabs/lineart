import json
import time

import click

from vulkan.cli.context import Context, pass_context


@click.group()
def policy():
    pass


@policy.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--description", type=str, default="", help="Description of the policy")
def create(ctx: Context, name: str, description: str):
    input_schema = "{}"
    response = ctx.session.post(
        f"{ctx.server_url}/policies",
        json={
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "output_schema": "",
        },
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create policy: {response.content}")
    policy_id = response.json()["policy_id"]
    ctx.logger.info(f"Created policy {name} with id {policy_id}")
    return policy_id


@policy.command()
@pass_context
@click.option("--policy_id", type=str)
@click.option("--policy_version_id", type=str)
def register_active_version(ctx: Context, policy_id: str, policy_version_id: str):
    response = ctx.session.put(
        f"{ctx.server_url}/policies/{policy_id}",
        json={"active_policy_version_id": policy_version_id},
    )
    if response.status_code != 200:
        raise ValueError("Failed to activate policy version")


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
        "ops": {"input_node": {"config": data}},
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
    for _ in range(timeout, step=step_size):
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
