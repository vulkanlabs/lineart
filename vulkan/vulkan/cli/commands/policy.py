import click

from vulkan.cli.context import Context, pass_context


@click.group()
def policy():
    pass


@policy.command()
@pass_context
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--description", type=str, default="", help="Description of the policy")
def create(ctx: Context, name: str, description: str):
    input_schema = "{}"
    response = ctx.session.post(
        f"{ctx.server_url}/policies",
        json={
            "name": name,
            "description": description,
            "input_schema": input_schema,
            "output_schema": "",
        },
    )
    if response.status_code != 200:
        raise ValueError(f"Failed to create policy: {response.content}")
    policy_id = response.json()["policy_id"]
    ctx.logger.info(f"Created policy {name} with id {policy_id}")
    return policy_id


@policy.command()
@pass_context
@click.option("--policy_id", type=str)
@click.option("--policy_version_id", type=str)
def register_active_version(ctx: Context, policy_id: str, policy_version_id: str):
    response = ctx.session.put(
        f"{ctx.server_url}/policies/{policy_id}",
        json={"active_policy_version_id": policy_version_id},
    )
    if response.status_code != 200:
        raise ValueError("Failed to activate policy version")
