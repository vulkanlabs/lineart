from dagster import JobExecutionResult, RunConfig, mem_io_manager

from vulkan.core.nodes import Node
from vulkan.core.policy import Policy
from vulkan.dagster.io_manager import PUBLISH_IO_MANAGER_KEY
from vulkan.dagster.policy import DagsterFlow
from vulkan.dagster.run_config import RUN_CONFIG_KEY, VulkanRunConfig

_TEST_RESOURCES = {
    RUN_CONFIG_KEY: VulkanRunConfig(policy_id=1, run_id=1, server_url=""),
    PUBLISH_IO_MANAGER_KEY: mem_io_manager,
}


def run_test_job(
    nodes: list[Node],
    input_schema: dict,
    run_config: dict,
) -> JobExecutionResult:
    config = RunConfig(ops=run_config)
    p = Policy(
        nodes=nodes,
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: None,
    )
    f = DagsterFlow(p.flattened_nodes, p.flattened_dependencies)
    job = f.to_job(resources=_TEST_RESOURCES)
    job_result = job.execute_in_process(run_config=config)
    return job_result
