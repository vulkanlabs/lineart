from vulkan.cli.client import backtest, policy, run
from vulkan.cli.context import Context

ctx = Context()

policy_id = policy.create_policy(ctx, name="Simple", description="Simple example")
policy_version_id = policy.create_policy_version(
    ctx,
    policy_id=policy_id,
    version_name="v0.0.1",
    repository_path="examples/policies/simple/",
)
policy.set_active_version(ctx, policy_id=policy_id, policy_version_id=policy_version_id)
ctx.logger.info(f"Created policy {policy_id} with version {policy_version_id}")

run.trigger_run_by_policy_version_id(
    ctx,
    policy_version_id=policy_version_id,
    input_data={"tax_id": "1", "score": 800},
    config_variables={"SCORE_CUTOFF": 700},
)

backtest.create_backtest(
    ctx,
    policy_version_id=policy_version_id,
    input_file_path="test/data/simple_bkt.csv",
    file_format="CSV",
    config_variables={"SCORE_CUTOFF": 700},
)
