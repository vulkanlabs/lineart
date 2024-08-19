import json
from enum import Enum

import pytest
from dagster import JobDefinition, RunConfig, mem_io_manager
from pytest_httpserver import HTTPServer

from vulkan_dagster.core.step_metadata import StepMetadata
from vulkan_dagster.core.dependency import Dependency
from vulkan_dagster.dagster import component
from vulkan_dagster.dagster.nodes import *
from vulkan_dagster.dagster.policy import *
from vulkan_dagster.dagster.io_manager import PUBLISH_IO_MANAGER_KEY
from vulkan_dagster.dagster.run_config import (
    RUN_CONFIG_KEY,
    VulkanRunConfig,
)


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

    job = _make_job([node], input_schema={"key": str})
    cfg = _make_run_config({"input_node": {"config": test_req_data}})
    job_result = job.execute_in_process(run_config=cfg)
    result = job_result._get_output_for_handle("http_connection", "result")
    assert result == test_resp_data


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

    job = _make_job([node], input_schema={"x": int})
    cfg = _make_run_config({"input_node": {"config": {"x": 10}}})
    job_result = job.execute_in_process(run_config=cfg)
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


class ExampleComponent(component.Component):
    def __init__(self, name, description, dependencies):
        node_a = Transform(
            name="a",
            description="Node A",
            func=lambda _, inputs: inputs,
            dependencies={"inputs": Dependency(self.make_input_node_name(name))},
        )
        node_b = Transform(
            name=self.make_output_node_name(name),
            description="Node B",
            func=lambda _, inputs: inputs["cpf"],
            dependencies={"inputs": Dependency(node_a.name)},
        )
        nodes = [node_a, node_b]
        input_schema = {"cpf": str}
        super().__init__(name, description, nodes, input_schema, dependencies)


def test_dagster_component():
    input_schema = {"cpf": str}
    component = ExampleComponent("component", "Component", {"cpf": Dependency("input_node")})

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
        dependencies={"inputs": Dependency(component.output_node_name)},
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

    policy = DagsterPolicy(
        nodes=[
            component,
            branch,
            approved,
            denied
        ],
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: "OK",
    )
    print("Nodes: ", [n.name for n in policy.nodes])
    print("Flattened Nodes: ", [n.name for n in policy.flattened_nodes])

    job = policy.to_job(resources=_TEST_RESOURCES)
    cfg = _make_run_config({"input_node": {"config": {"cpf": "1"}}})
    job_result = job.execute_in_process(run_config=cfg)
    result = job_result._get_output_for_handle("approved", "result")
    assert result == ReturnStatus.APPROVED.value


_TEST_RESOURCES = {
    RUN_CONFIG_KEY: VulkanRunConfig(policy_id=1, run_id=1, server_url="dummy"),
    PUBLISH_IO_MANAGER_KEY: mem_io_manager,
}


def _make_job(ops: list[DagsterNode], input_schema: dict) -> JobDefinition:
    p = DagsterPolicy(
        nodes=ops,
        input_schema=input_schema,
        output_callback=lambda _, **kwargs: None,
    )
    return p.to_job(resources=_TEST_RESOURCES)


def _make_run_config(ops: dict) -> RunConfig:
    return RunConfig(ops=ops)
