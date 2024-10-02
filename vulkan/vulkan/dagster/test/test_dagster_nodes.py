import json
from enum import Enum

from pytest_httpserver import HTTPServer
from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import (
    HTTPConnectionNode,
    NodeType,
    TerminateNode,
    TransformNode,
)

from vulkan.core.step_metadata import StepMetadata
from vulkan.dagster.nodes import to_dagster_node
from vulkan.dagster.testing import run_test_job


def test_http_connection(httpserver: HTTPServer):
    test_req_data = {"key": "value"}
    test_resp_data = {"resp_key": "resp_value"}

    node = HTTPConnectionNode(
        name="http_connection",
        description="HTTP connection",
        url=httpserver.url_for("/"),
        method="GET",
        headers={"Content-Type": "application/json"},
        params={"param": "value", "param2": "value2"},
        dependencies={"body": Dependency("input_node")},
    )

    assert len(node.dependencies) == 1

    dagster_node = to_dagster_node(node)
    dagster_op = dagster_node.op()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "metadata",
        "result",
    }, "Should have two outputs named 'metadata' and 'result'"

    httpserver.expect_oneshot_request(
        "/",
        method="GET",
        json=test_req_data,
        headers={"Content-Type": "application/json"},
        query_string="param=value&param2=value2",
    ).respond_with_json(test_resp_data)

    job_result = run_test_job(
        nodes=[node],
        input_schema={"key": str},
        run_config={"input_node": {"config": test_req_data}},
    )
    result = job_result._get_output_for_handle("http_connection", "result")
    assert json.loads(result) == test_resp_data


def test_transform():
    node = TransformNode(
        name="transform",
        description="Transform node",
        func=lambda _, inputs: inputs["x"] * 2,
        dependencies={"inputs": Dependency("input_node")},
    )

    assert len(node.dependencies) == 1

    dagster_node = to_dagster_node(node)
    dagster_op = dagster_node.op()
    assert len(dagster_op.ins) == 1
    assert set(dagster_op.outs.keys()) == {
        "result",
        "metadata",
    }, "Should have two outputs 'result' and 'metadata'"

    job_result = run_test_job(
        [node],
        input_schema={"x": int},
        run_config={"input_node": {"config": {"x": 10}}},
    )
    result = job_result._get_output_for_handle("transform", "result")
    assert result == 20
    metadata = job_result._get_output_for_handle("transform", "metadata")
    assert isinstance(metadata, StepMetadata)
    assert metadata.error is None


class ReturnStatus(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


def test_terminate():
    terminate = TerminateNode(
        name="terminate",
        description="Terminate node",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value
