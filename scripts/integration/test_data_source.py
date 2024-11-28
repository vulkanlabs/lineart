from vulkan_public.cli.client import component, policy, data, run
from vulkan_public.cli.context import Context

ctx = Context()

data.create_data_source(ctx, config_path="examples/data/vendor_data_example.yaml")

policy_id = policy.create_policy(ctx, name="Vendor Data", description="Vendor Data demo policy", input_schema="{}", output_schema="{}")
policy_version_id = policy.create_policy_version(ctx, policy_id=policy_id, version_name="v0.0.1", repository_path="examples/policies/data_input/")
policy.set_active_version(ctx, policy_id=policy_id, policy_version_id=policy_version_id)
ctx.logger.info(f"Created policy {policy_id} with version {policy_version_id}")

run.trigger_run_by_policy_id(ctx, policy_id=policy_id, input_data={"cpf": "1"})

component_id = component.create_component(ctx, name="vendor_data")
component_version_id = component.create_component_version(
    ctx,
    component_id=component_id,
    version_name="v0.0.1",
    repository_path="examples/components/vendor_data/",
)

policy_id = policy.create_policy(ctx, name="Vendor Data Comp", description="Vendor Data with component demo policy", input_schema="{}", output_schema="{}")
policy_version_id = policy.create_policy_version(ctx, policy_id=policy_id, version_name="v0.0.1", repository_path="examples/policies/data_input_comp/")
policy.set_active_version(ctx, policy_id=policy_id, policy_version_id=policy_version_id)
ctx.logger.info(f"Created policy {policy_id} with version {policy_version_id}")

run.trigger_run_by_policy_id(ctx, policy_id=policy_id, input_data={"cpf": "1"})