from dagster import JobExecutionResult, RunConfig, mem_io_manager

from vulkan_dagster.dagster.io_manager import PUBLISH_IO_MANAGER_KEY
from vulkan_dagster.dagster.nodes import DagsterNode
from vulkan_dagster.dagster.policy import DagsterPolicy
from vulkan_dagster.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig

_TEST_RESOURCES = {
    RUN_CONFIG_KEY: VulkanRunConfig(policy_id=1, run_id=1, server_url=""),
    PUBLISH_IO_MANAGER_KEY: mem_io_manager,
}


def run_test_job(
    ops: list[DagsterNode],
    input_schema: dict,
    run_config: dict,
) -> JobExecutionResult:
    config = RunConfig(ops=run_config)
    p = DagsterPolicy(
        nodes=ops,
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: None,
    )
    job = p.to_job(resources=_TEST_RESOURCES)
    job_result = job.execute_in_process(run_config=config)
    return job_result
