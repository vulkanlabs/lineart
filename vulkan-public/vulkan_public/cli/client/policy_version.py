from vulkan_public.cli.context import Context


def list_variables(ctx: Context, policy_version_id: str) -> dict[str, str | None]:
    response = ctx.session.get(
        f"{ctx.server_url}/policy-versions/{policy_version_id}/variables",
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list variables: {response.content}")
    return response.json()


def set_variables(
    ctx: Context,
    policy_version_id: str,
    variables: dict[str, str],
):
    ctx.logger.info(f"Setting variables: {variables}")
    response = ctx.session.put(
        f"{ctx.server_url}/policy-versions/{policy_version_id}/variables",
        json=variables,
    )
    if response.status_code != 200:
        raise ValueError("Failed to set variables")

    return response.json()


def create_backtest_workspace(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.post(
        f"{ctx.server_url}/policy-versions/{policy_version_id}/backtest-workspace"
    )

    assert (
        response.status_code == 200
    ), f"Failed to create backtest workspace: {response.content}"
    return response.json()


def get_policy_version_graph(ctx: Context, policy_version_id: str):
    response = ctx.session.get(f"{ctx.server_url}/policy-versions/{policy_version_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to get policy version graph: {response.content}")
    return response.json()["graph_definition"]


def delete_policy_version(
    ctx: Context,
    policy_version_id: str,
):
    response = ctx.session.delete(
        f"{ctx.server_url}/policy-versions/{policy_version_id}"
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to delete policy version: {response.content}")
    ctx.logger.info(f"Deleted policy version {policy_version_id}")
