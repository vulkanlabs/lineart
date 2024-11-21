import builtins
import json
import os

from pandas import DataFrame

from vulkan_public.cli.context import Context


def create_backtest(
    ctx: Context,
    policy_version_id: str,
    input_file_id: str,
    config_variables: list[dict] | None = None,
):
    response = ctx.session.post(
        f"{ctx.server_url}/backtests/launch",
        json={
            "policy_version_id": policy_version_id,
            "input_file_id": input_file_id,
            "config_variables": config_variables,
        },
        # "file_format": file_format,
        # files={"input_file": open(input_file_path, "rb")},
    )
    assert response.status_code == 200, f"Failed to create backtest: {response.content}"
    response_data = response.json()
    backtest_id = response_data["backtest_id"]
    ctx.logger.info(f"Created backtest with id {backtest_id}")
    return response_data


def create_workspace(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.post(
        f"{ctx.server_url}/backtests/",
        params={"policy_version_id": policy_version_id},
    )

    assert response.status_code == 200, f"Failed to create backtest: {response.content}"
    return response.json()


def get_results(ctx: Context, backtest_id: str):
    url = f"{ctx.server_url}/backtests/{backtest_id}/results"
    response = ctx.session.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get backfill results: {response.content}")
    return DataFrame(response.json())


def upload_backtest_file(
    ctx: Context,
    file_path: str,
    file_format: str,
    schema: dict[str, str],
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
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    if file_format not in ["CSV", "PARQUET"]:
        raise ValueError(f"Unsupported file format: {file_format}")

    if not isinstance(schema, dict):
        raise ValueError(f"Schema must be a dict: {schema}")

    response = ctx.session.post(
        f"{ctx.server_url}/backtests/files",
        files={"file": open(file_path, "rb")},
        data={
            "file_format": file_format,
            "schema": _serialize_schema(schema),
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
