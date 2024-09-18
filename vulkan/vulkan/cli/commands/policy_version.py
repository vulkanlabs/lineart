import click

from vulkan.cli.context import Context, pass_context
from vulkan.cli.client import policy_version


@click.command()
@pass_context
@click.option("--policy_id", type=str, required=True, help="Id of the policy")
@click.option("--name", type=str, required=True, help="Name of the policy")
@click.option("--repository_path", type=str, required=True, help="Path to repository")
def create_policy_version(
    ctx: Context,
    policy_id: str,
    name: str,
    repository_path: str,
):
    return policy_version.create(ctx, policy_id, name, repository_path)
