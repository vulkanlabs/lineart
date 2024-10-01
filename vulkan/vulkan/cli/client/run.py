import json
import time

from vulkan.cli.context import Context


def trigger_run_by_policy_id(
    ctx: Context,
    policy_id: str,
    input_data: dict,
    timeout: int = 15,
    time_step: int = 5,
):
    execution_config = {
        "ops": {"input_node": {"config": input_data}},
    }
    ctx.logger.debug(f"Execution config: {execution_config}")

    response = ctx.session.post(
        f"{ctx.server_url}/policies/{policy_id}/runs",
        json={"execution_config_str": json.dumps(execution_config)},
    )
    if response.status_code == 404:
        msg = (
            f"No policy with id {policy_id} found.\n"
            "Check the policy id and try again."
        )
        raise ValueError(msg)
    if response.status_code != 200:
        msg = f"Error triggering run for policy {policy_id}. \n{response.text}"
        raise ValueError(msg)

    # Get the run status
    run_id = response.json()["run_id"]
    response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}")
    ctx.logger.debug(response.json())

    success = False
    # Poll the API until the job is completed
    for _ in range(0, timeout, time_step):
        response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}")
        ctx.logger.debug(response.json())
        try:
            status = response.json()["status"]
            if status == "SUCCESS":
                success = True
                break
            elif status == "FAILURE":
                break
        except (KeyError, json.decoder.JSONDecodeError):
            continue
        time.sleep(time_step)

    return run_id, success


def get_run_data(ctx: Context, run_id: str):
    response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}/data")
    if response.status_code == 404:
        msg = f"No run with id {run_id} found.\nCheck the run id and try again."
        raise ValueError(msg)
    if response.status_code != 200:
        msg = f"Error fetching run data for run {run_id}. \n{response.text}"
        raise ValueError

    return response.json()
