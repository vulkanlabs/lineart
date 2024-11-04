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
    return response.json()
