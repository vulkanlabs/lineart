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
    ctx: Context, policy_version_id: str, input_file_path: str, file_format: str
):
    response = ctx.session.post(
        f"{ctx.server_url}/backtests",
        params={
            "policy_version_id": policy_version_id,
            "file_format": file_format,
            "config_variables": {},
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


def create_workspace(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.post(
        f"{ctx.server_url}/backtests/create_workspace",
        params={"policy_version_id": policy_version_id},
    )

    assert response.status_code == 200, f"Failed to create backtest: {response.content}"
    return response.json()


def download_results_to_file(ctx: Context, backtest_id: str, filename: str):
    url = f"{ctx.server_url}/backtests/{backtest_id}/results"
    response = ctx.session.get(url, stream=True)

    with open(filename, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    ctx.logger.info(f"Downloaded results to {filename}")
