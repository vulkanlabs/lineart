from enum import Enum

from vulkan_public.spec.dependency import Dependency
from vulkan_public.spec.nodes import NodeType, TerminateNode, TransformNode

from vulkan.core.step_metadata import StepMetadata
from vulkan.dagster.nodes import to_dagster_node
from vulkan.dagster.testing import run_test_job


def test_dagster_transform():
    node = TransformNode(
        name="transform",
        description="Transform node",
        func=lambda context, inputs: inputs["x"] * 2,
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


def test_dagster_terminate():
    terminate = TerminateNode(
        name="terminate",
        description="Terminate node",
        return_status=ReturnStatus.APPROVED,
        dependencies={"inputs": Dependency("input_node")},
    )
    definition = terminate.node_definition()
    assert definition.node_type == NodeType.TERMINATE.value
