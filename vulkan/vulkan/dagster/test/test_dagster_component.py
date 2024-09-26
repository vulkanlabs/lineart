from enum import Enum

from vulkan.core.component import ComponentGraph
from vulkan.dagster.testing import run_test_job
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import BranchNode, TransformNode


class ReturnStatus(Enum):
    APPROVED = "APPROVED"
    DENIED = "DENIED"


class ExampleComponent(ComponentGraph):
    def __init__(self, name, description, dependencies):
        node_a = TransformNode(
            name="a",
            description="Node A",
            func=lambda _, inputs: inputs,
            dependencies={"inputs": Dependency("input_node")},
        )
        node_b = TransformNode(
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

    branch = BranchNode(
        "branch",
        func=branch_fn,
        outputs=[ReturnStatus.APPROVED.value, ReturnStatus.DENIED.value],
        dependencies={"inputs": Dependency(component.name)},
    )

    approved = TransformNode(
        "approved",
        func=lambda _, inputs: ReturnStatus.APPROVED.value,
        dependencies={"inputs": Dependency(branch.name, ReturnStatus.APPROVED.value)},
    )

    denied = TransformNode(
        "denied",
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
