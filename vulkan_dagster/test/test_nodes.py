import json

import pytest
from dagster import JobDefinition, OpDefinition, RunConfig, mem_io_manager
from pytest_httpserver import HTTPServer

from vulkan_dagster import nodes, policy
from vulkan_dagster.run import RUN_CONFIG_KEY, VulkanRunConfig
from vulkan_dagster.step_metadata import PUBLISH_IO_MANAGER_KEY, StepMetadata


def test_http_connection(httpserver: HTTPServer):
    test_req_data = {"key": "value"}
    test_resp_data = {"resp_key": "resp_value"}

    node = nodes.HTTPConnection(
        name="http_connection",
        description="HTTP connection",
        url=httpserver.url_for("/"),
        method="GET",
        headers={"Content-Type": "application/json"},
        params={"param": "value", "param2": "value2"},
        dependencies={"body": "input_node"},
    )

    assert len(node.graph_dependencies()) == 1

    dagster_op = node.node()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "result"
    }, "Should have a single output named 'result'"

    httpserver.expect_oneshot_request(
        "/",
        method="GET",
        json=test_req_data,
        headers={"Content-Type": "application/json"},
        query_string="param=value&param2=value2",
    ).respond_with_json(test_resp_data)

    job = _make_job([node], input_schema={"key": str})
    cfg = _make_run_config({"input_node": {"config": test_req_data}})
    job_result = job.execute_in_process(run_config=cfg)
    result = job_result._get_output_for_handle("http_connection", "result")
    assert result == test_resp_data


def test_transform():
    node = nodes.Transform(
        name="transform",
        description="Transform node",
        func=lambda context, inputs: inputs["x"] * 2,
        dependencies={"inputs": "input_node"},
    )

    assert len(node.graph_dependencies()) == 1

    dagster_op = node.node()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "result",
        "metadata",
    }, "Should have two outputs 'result' and 'metadata'"

    job = _make_job([node], input_schema={"x": int})
    cfg = _make_run_config({"input_node": {"config": {"x": 10}}})
    job_result = job.execute_in_process(run_config=cfg)
    result = job_result._get_output_for_handle("transform", "result")
    assert result == 20
    metadata = job_result._get_output_for_handle("transform", "metadata")
    assert isinstance(metadata, StepMetadata)
    assert metadata.error is None


_TEST_RESOURCES = {
    RUN_CONFIG_KEY: VulkanRunConfig(policy_id=1, run_id=1, server_url="dummy"),
    PUBLISH_IO_MANAGER_KEY: mem_io_manager,
}


def _make_job(ops: list[nodes.Node], input_schema: dict) -> JobDefinition:
    p = policy.Policy(
        name="test_policy",
        description="Test policy",
        nodes=ops,
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: None,
    )
    return p.to_job(resources=_TEST_RESOURCES)


def _make_run_config(ops: dict) -> RunConfig:
    return RunConfig(ops=ops)
