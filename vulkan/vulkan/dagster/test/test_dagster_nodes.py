import json
from enum import Enum

from pytest_httpserver import HTTPServer

from vulkan.core.dependency import Dependency
from vulkan.core.nodes import NodeType
from vulkan.core.step_metadata import StepMetadata
from vulkan.dagster import component
from vulkan.dagster.nodes import *
from vulkan.dagster.policy import *
from vulkan.dagster.testing import run_test_job


def test_http_connection(httpserver: HTTPServer):
    test_req_data = {"key": "value"}
    test_resp_data = {"resp_key": "resp_value"}

    node = HTTPConnection(
        name="http_connection",
        description="HTTP connection",
        url=httpserver.url_for("/"),
        method="GET",
        headers={"Content-Type": "application/json"},
        params={"param": "value", "param2": "value2"},
        dependencies={"body": Dependency("input_node")},
    )

    assert len(node.dependencies) == 1

    dagster_op = node.op()
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

    job_result = run_test_job(
        ops=[node],
        input_schema={"key": str},
        run_config={"input_node": {"config": test_req_data}},
    )
    result = job_result._get_output_for_handle("http_connection", "result")
    assert json.loads(result) == test_resp_data


def test_transform():
    node = Transform(
        name="transform",
        description="Transform node",
        func=lambda _, inputs: inputs["x"] * 2,
        dependencies={"inputs": Dependency("input_node")},
    )

    assert len(node.dependencies) == 1

    dagster_op = node.op()
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
    terminate = Terminate(
        name="terminate",
        description="Terminate node",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value


class ExampleComponent(component.DagsterComponent):
    def __init__(self, name, description, dependencies):
        node_a = Transform(
            name="a",
            description="Node A",
            func=lambda _, inputs: inputs,
            dependencies={"inputs": Dependency("input_node")},
        )
        node_b = Transform(
            name="b",
            description="Node B",
            func=lambda _, inputs: inputs["cpf"],
            dependencies={"inputs": Dependency(node_a.name)},
        )
        nodes = [node_a, node_b]
        input_schema = {"cpf": str}
        super().__init__(name, description, nodes, input_schema, dependencies)


def test_dagster_component():
    input_schema = {"cpf": str}
    component = ExampleComponent(
        "component", "Component", {"cpf": Dependency("input_node")}
    )

    def branch_fn(context, inputs: dict):
        context.log.info(f"Branching with inputs {inputs}")
        if inputs["cpf"] == "1":
            return ReturnStatus.APPROVED.value
        return ReturnStatus.DENIED.value

    branch = Branch(
        "branch",
        "Branch Node",
        func=branch_fn,
        outputs=[ReturnStatus.APPROVED.value, ReturnStatus.DENIED.value],
        dependencies={"inputs": Dependency(component.name)},
    )

    approved = Transform(
        "approved",
        "Approved",
        func=lambda _, inputs: ReturnStatus.APPROVED.value,
        dependencies={"inputs": Dependency(branch.name, ReturnStatus.APPROVED.value)},
    )

    denied = Transform(
        "denied",
        "Denied",
        func=lambda _, inputs: ReturnStatus.DENIED.value,
        dependencies={"inputs": Dependency(branch.name, ReturnStatus.DENIED.value)},
    )

    job_result = run_test_job(
        [component, branch, approved, denied],
        input_schema,
        run_config={"input_node": {"config": {"cpf": "1"}}},
    )
    result = job_result._get_output_for_handle("approved", "result")
    assert result == ReturnStatus.APPROVED.value
