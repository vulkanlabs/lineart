from vulkan_public.cli.context import Context


def list_variables(ctx: Context, policy_version_id: str) -> dict[str, str | None]:
    response = ctx.session.get(
        f"{ctx.server_url}/policyVersions/{policy_version_id}/variables",
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list variables: {response.content}")
    return response.json()


def set_variables(
    ctx: Context,
    policy_version_id: str,
    variables: dict[str, str],
):
    response = ctx.session.put(
        f"{ctx.server_url}/policyVersions/{policy_version_id}/variables",
        json=variables,
    )
    if response.status_code != 200:
        raise ValueError("Failed to set variables")

    return response.json()
