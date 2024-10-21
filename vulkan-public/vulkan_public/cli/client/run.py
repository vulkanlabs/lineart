import json
import time

from vulkan_public.cli.context import Context


class RunLauncher:
    def __init__(
        self,
        ctx: Context,
        input_data: dict,
        timeout: int = 15,
        time_step: int = 5,
    ):
        self.ctx = ctx
        self.timeout = timeout
        self.time_step = time_step
        self.execution_config = {"ops": {"input_node": {"config": input_data}}}

    def trigger_run_by_policy_id(self, policy_id: str):
        run_id = self._launch_run_by_policy_id(policy_id)
        success = self.poll_run_status(run_id)
        return run_id, success

    def trigger_run_by_policy_version_id(self, policy_version_id: str):
        run_id = self._launch_run_by_policy_version_id(policy_version_id)
        success = self.poll_run_status(run_id)
        return run_id, success

    def poll_run_status(self, run_id: str):
        url = f"{self.ctx.server_url}/runs/{run_id}"

        # Get the run status
        response = self.ctx.session.get(url)
        self.ctx.logger.debug(response.json())

        success = False
        # Poll the API until the job is completed
        for _ in range(0, self.timeout, self.time_step):
            response = self.ctx.session.get(url)
            self.ctx.logger.debug(response.json())
            try:
                status = response.json()["status"]
                if status == "SUCCESS":
                    success = True
                    break
                elif status == "FAILURE":
                    break
            except (KeyError, json.decoder.JSONDecodeError):
                continue
            time.sleep(self.time_step)

        return success

    def _launch_run_by_policy_id(self, policy_id: str):
        response = self.__launch_run(
            url=f"{self.ctx.server_url}/policies/{policy_id}/runs"
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

        return response.json()["run_id"]

    def _launch_run_by_policy_version_id(self, policy_version_id: str):
        response = self.__launch_run(
            url=f"{self.ctx.server_url}/policy-versions/{policy_version_id}/runs"
        )
        if response.status_code == 404:
            msg = (
                f"No policy version with id {policy_version_id} found.\n"
                "Check the policy version id and try again."
            )
            raise ValueError(msg)
        if response.status_code != 200:
            msg = (
                f"Error triggering run for policy version {policy_version_id}. "
                f"\n{response.text}"
            )
            raise ValueError(msg)

        return response.json()["run_id"]

    def __launch_run(self, url: str):
        self.ctx.logger.debug(
            f"Lanching run with execution config: {self.execution_config}"
        )
        body = {"execution_config_str": json.dumps(self.execution_config)}
        return self.ctx.session.post(url, json=body)


def trigger_run_by_policy_id(
    ctx: Context,
    policy_id: str,
    input_data: dict,
    timeout: int = 15,
    time_step: int = 5,
):
    laucher = RunLauncher(ctx, input_data, timeout, time_step)
    return laucher.trigger_run_by_policy_id(policy_id)


def trigger_run_by_policy_version_id(
    ctx: Context,
    policy_version_id: str,
    input_data: dict,
    timeout: int = 15,
    time_step: int = 5,
):
    laucher = RunLauncher(ctx, input_data, timeout, time_step)
    return laucher.trigger_run_by_policy_version_id(policy_version_id)


def get_run_data(ctx: Context, run_id: str):
    response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}/data")
    if response.status_code == 404:
        msg = f"No run with id {run_id} found.\nCheck the run id and try again."
        raise ValueError(msg)
    if response.status_code != 200:
        msg = f"Error fetching run data for run {run_id}. \n{response.text}"
        raise ValueError

    return response.json()


def get_run_logs(ctx: Context, run_id: str):
    response = ctx.session.get(f"{ctx.server_url}/runs/{run_id}/logs")
    if response.status_code == 404:
        msg = f"No run with id {run_id} found.\nCheck the run id and try again."
        raise ValueError(msg)
    if response.status_code != 200:
        msg = f"Error fetching logs for run {run_id}. \n{response.text}"
        raise ValueError

    return response.json()
