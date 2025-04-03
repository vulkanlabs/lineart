from vulkan_public.cli.context import Context
from vulkan_public.schemas import PolicyAllocationStrategy


def list_policies(ctx: Context, include_archived: bool = False):
    response = ctx.session.get(
        f"{ctx.server_url}/policies", params={"include_archived": include_archived}
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list policies: {response.content}")
    return response.json()


def create_policy(
    ctx: Context,
    name: str,
    description: str = "",
):
    response = ctx.session.post(
        f"{ctx.server_url}/policies",
        json={"name": name, "description": description},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create policy: {response.content}")

    policy_id = response.json()["policy_id"]
    ctx.logger.info(f"Created policy {name} with id {policy_id}")
    return policy_id


def set_allocation_strategy(ctx: Context, policy_id: str, allocation_strategy: dict):
    strategy = PolicyAllocationStrategy.model_validate(allocation_strategy)
    response = ctx.session.put(
        f"{ctx.server_url}/policies/{policy_id}",
        json={"allocation_strategy": strategy.model_dump()},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to set allocation strategy: {response.content}")
    return response.json()


def delete_policy(ctx: Context, policy_id: str):
    response = ctx.session.delete(f"{ctx.server_url}/policies/{policy_id}")
    if response.status_code != 200:
        raise ValueError(f"Failed to delete policy: {response.content}")
    ctx.logger.info(f"Deleted policy {policy_id}")


def list_runs_by_policy(ctx: Context, policy_id: str):
    response = ctx.session.get(f"{ctx.server_url}/policies/{policy_id}/runs")
    if response.status_code != 200:
        raise ValueError(f"Failed to list runs: {response.content}")
    return response.json()


def list_policy_versions(ctx: Context, policy_id: str, include_archived: bool = False):
    response = ctx.session.get(
        f"{ctx.server_url}/policies/{policy_id}/versions",
        params={"include_archived": include_archived},
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to list policy versions: {response.content}")
    return response.json()
