import builtins
import json
import os
import time

from pandas import DataFrame

from vulkan_public.cli.context import Context


def list_backtests(ctx: Context):
    response = ctx.session.get(f"{ctx.server_url}/backtests")
    assert response.status_code == 200, f"Failed to list backtests: {response.content}"
    return response.json()


def create_backtest(
    ctx: Context,
    policy_version_id: str,
    input_file_id: str,
    config_variables: list[dict] | None = None,
    metrics_config: dict | None = None,
):
    ctx.logger.info("Creating backtest. This may take a while...")
    response = ctx.session.post(
        f"{ctx.server_url}/backtests/",
        json={
            "policy_version_id": policy_version_id,
            "input_file_id": input_file_id,
            "config_variables": config_variables,
            "metrics_config": metrics_config,
        },
    )
    assert response.status_code == 200, f"Failed to create backtest: {response.content}"
    response_data = response.json()
    backtest_id = response_data["backtest_id"]
    ctx.logger.info(f"Created backtest with id {backtest_id}")
    return response_data


def create_backtest_metrics(
    ctx: Context,
    backtest_id: str,
):
    ctx.logger.info("Creating backtest metrics...")
    response = ctx.session.post(
        f"{ctx.server_url}/backtests/{backtest_id}/metrics",
    )
    assert (
        response.status_code == 200
    ), f"Failed to create backtest metrics: {response.content}"
    return response.json()


def get_backtest_status(ctx: Context, backtest_id: str):
    response = ctx.session.get(f"{ctx.server_url}/backtests/{backtest_id}/status")
    assert (
        response.status_code == 200
    ), f"Failed to get backtest state: {response.content}"
    return response.json()


def poll_backtest_status(
    ctx: Context, backtest_id: str, timeout: int = 300, time_step: int = 30
):
    for _ in range(0, timeout, time_step):
        backtest_status = get_backtest_status(ctx, backtest_id)
        ctx.logger.info(backtest_status)

        if backtest_status["status"] == "DONE":
            break

        time.sleep(time_step)
    return backtest_status


def get_backtest_metrics_job_status(ctx: Context, backtest_id: str):
    response = ctx.session.get(f"{ctx.server_url}/backtests/{backtest_id}/metrics")
    assert (
        response.status_code == 200
    ), f"Failed to get backtest state: {response.content}"
    return response.json()


def poll_backtest_metrics_job_status(
    ctx: Context, backtest_id: str, timeout: int = 300, time_step: int = 30
):
    terminal_states = {"SUCCESS", "FAILURE"}
    for _ in range(0, timeout, time_step):
        jobs_status = get_backtest_metrics_job_status(ctx, backtest_id)
        ctx.logger.info(jobs_status)

        if jobs_status["status"] in terminal_states:
            break
        time.sleep(time_step)
    return jobs_status


def get_results(ctx: Context, backtest_id: str):
    url = f"{ctx.server_url}/backtests/{backtest_id}/results"
    response = ctx.session.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get backfill results: {response.content}")
    return DataFrame(response.json())


def list_uploaded_files(ctx: Context, file_name: str | None = None):
    if file_name:
        params = {"file_name": file_name}

    response = ctx.session.get(
        f"{ctx.server_url}/files",
        params=params,
    )
    assert (
        response.status_code == 200
    ), f"Failed to list uploaded files: {response.content}"
    return response.json()


def upload_backtest_file(
    ctx: Context,
    file_path: str,
    file_format: str,
    schema: dict[str, str],
    file_name: str | None = None,
):
    """Upload a file to the backtest service.

    Parameters
    ----------
    ctx : Context
        The context object.
    file_path : str
        The path to the file to upload.
    file_format : str
        The format of the file. Currently, only "CSV"
        and "PARQUET" are supported.
    schema : dict[str, str]
        A dictionary mapping column names to their types.
        Only built-in types are currently supported and
        they must be specified as strings.
        E.g. {"column1": "int", "column2": "str"}
    policy_version_id : str
        The ID of the policy version associated with the file.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_format not in ["CSV", "PARQUET"]:
        raise ValueError(f"Unsupported file format: {file_format}")

    if not isinstance(schema, dict):
        raise ValueError(f"Schema must be a dict: {schema}")

    response = ctx.session.post(
        f"{ctx.server_url}/files",
        files={"file": open(file_path, "rb")},
        data={
            "file_format": file_format,
            "schema": _serialize_schema(schema),
            "file_name": file_name,
        },
    )
    assert response.status_code == 200, f"Failed to upload file: {response.content}"
    return response.json()


def _serialize_schema(schema: dict[str, str]) -> str:
    invalid_types = []
    for key, value in schema.items():
        try:
            _ = getattr(builtins, value)
        except (AttributeError, TypeError):
            invalid_types.append({key: value})

    if invalid_types:
        raise ValueError(
            f"Unsupported schema types: {invalid_types}. Only built-in "
            "types (specified as strings) are supported."
        )

    return json.dumps(schema)
