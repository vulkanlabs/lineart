import builtins
import json
import os

from vulkan_public.cli.context import Context


def list_backtests(ctx: Context):
    response = ctx.session.get(f"{ctx.server_url}/backtests")
    assert response.status_code == 200, f"Failed to list backtests: {response.content}"
    return response.json()


def get_backtest(ctx: Context, backtest_id: str):
    response = ctx.session.get(f"{ctx.server_url}/backtests/{backtest_id}")
    assert response.status_code == 200, f"Failed to list backtests: {response.content}"
    return response.json()


def create_backtest(
    ctx: Context,
    policy_version_id: str,
    input_file_path: str,
    file_format: str,
    config_variables: dict | None = None,
):
    response = ctx.session.post(
        f"{ctx.server_url}/backtests",
        params={
            "policy_version_id": policy_version_id,
            "file_format": file_format,
            "config_variables": json.dumps(config_variables),
        },
        files={"input_file": open(input_file_path, "rb")},
    )
    assert response.status_code == 200, f"Failed to create backtest: {response.content}"
    response_data = response.json()
    backtest_id = response_data["backtest_id"]
    ctx.logger.info(f"Created backtest with id {backtest_id}")
    return response_data


def get_backtest_results(ctx: Context, backtest_id: str):
    url = f"{ctx.server_url}/backtests/{backtest_id}/results"
    response = ctx.session.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to get backtest results: {response.content}")
    return response.json()


def download_results_to_file(ctx: Context, backtest_id: str, filename: str):
    url = f"{ctx.server_url}/backtests/{backtest_id}/results"
    response = ctx.session.get(url, stream=True)

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    ctx.logger.info(f"Downloaded results to {filename}")


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
