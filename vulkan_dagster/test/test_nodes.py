import json

import pytest
from dagster import JobDefinition, OpDefinition, RunConfig
from pytest_httpserver import HTTPServer

from vulkan_dagster import nodes, policy
from vulkan_dagster.run import RUN_CONFIG_KEY, VulkanRunConfig


def test_http_connection(httpserver: HTTPServer):
    test_req_data = {"key": "value"}
    test_resp_data = {"resp_key": "resp_value"}
    httpserver.expect_oneshot_request(
        "/",
        method="GET",
        json=test_req_data,
        headers={"Content-Type": "application/json"},
    ).respond_with_json(test_resp_data)

    node = nodes.HTTPConnection(
        name="http_connection",
        description="HTTP connection",
        url=httpserver.url_for("/"),
        method="GET",
        headers={"Content-Type": "application/json"},
        dependencies={"body": "input_node"},
    )

    assert len(node.graph_dependencies()) == 1

    dagster_op = node.node()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "result"
    }, "Should have a single output named 'result'"

    job = _make_job([node], input_schema={"key": str})
    cfg = _make_run_config({"input_node": {"config": test_req_data}})
    job_result = job.execute_in_process(run_config=cfg)
    result = job_result._get_output_for_handle("http_connection", "result")
    # result = dagster_op(ctx, {"body": test_req_data})
    assert result == test_resp_data


TEST_RESOURCES = {
    RUN_CONFIG_KEY: VulkanRunConfig(policy_id=1, run_id=1, server_url="dummy")
}


def _make_job(ops: list[nodes.Node], input_schema: dict) -> JobDefinition:
    p = policy.Policy(
        name="test_policy",
        description="Test policy",
        nodes=ops,
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: None,
    )
    return p.to_job(resources=TEST_RESOURCES)


def _make_run_config(ops: dict) -> RunConfig:
    return RunConfig(ops=ops)
