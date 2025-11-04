import apache_beam as beam
from apache_beam.testing.test_pipeline import TestPipeline
from vulkan.core.policy import Policy
from vulkan.runners.beam.io import ReadLocalCSV
from vulkan.runners.beam.nodes import (
    BeamBranch,
    BeamInput,
    BeamTerminate,
    to_beam_nodes,
)
from vulkan.runners.beam.pipeline import build_pipeline
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.graph import sort_nodes
from vulkan.spec.nodes import BranchNode, NodeType, TerminateNode, TransformNode
from vulkan.spec.policy import PolicyDefinition


def test_pipeline():
    input_node = BeamInput(
        name=INPUT_NODE,
        schema={"score": int},
        data_path="vulkan/vulkan/runners/beam/test/input_data.csv",
    )

    def _branch(data):
        print(data)
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        func=_branch,
        choices=["approved", "denied"],
        dependencies={"data": Dependency(input_node.name)},
    )

    approved = BeamTerminate(
        name="approved",
        return_status="approved",
        dependencies={"condition": Dependency(branch.name, "approved")},
    )
    denied = BeamTerminate(
        name="denied",
        return_status="denied",
        dependencies={"condition": Dependency(branch.name, "denied")},
    )

    with TestPipeline() as pipeline:
        input_data = pipeline | "Read Input" >> ReadLocalCSV(input_node.data_path)
        collections = {INPUT_NODE: input_data}

        output, _ = build_pipeline(pipeline, collections, [branch, approved, denied])
        output | "Print" >> beam.Map(print)


def test_pipeline_from_policy():
    def _transform(data):
        data["p_score"] = data["score"] / 1000
        return data

    transform = TransformNode(
        name="transform",
        func=_transform,
        dependencies={"data": Dependency(INPUT_NODE)},
    )

    def _branch(data):
        if data["p_score"] > 0.5:
            return "approved"
        return "denied"

    branch = BranchNode(
        name="branch",
        func=_branch,
        choices=["approved", "denied"],
        dependencies={"data": Dependency(transform.name)},
    )

    approved = TerminateNode(
        name="approved",
        return_status="approved",
        dependencies={"condition": Dependency(branch.name, "approved")},
    )
    denied = TerminateNode(
        name="denied",
        return_status="denied",
        dependencies={"condition": Dependency(branch.name, "denied")},
    )

    definition = PolicyDefinition(
        nodes=[transform, branch, approved, denied],
        input_schema={"data": dict},
    )
    policy = Policy.from_definition(definition)
    nodes = policy.nodes
    edges = policy.edges

    input_node = [node for node in nodes if node.type == NodeType.INPUT][0]
    core_nodes = [node for node in nodes if node.type != NodeType.INPUT]

    beam_input = BeamInput.from_spec(
        input_node, data_path="vulkan/vulkan/runners/beam/test/input_data.csv"
    )
    beam_nodes = to_beam_nodes(core_nodes)
    sorted_nodes = sort_nodes(beam_nodes, edges)

    with TestPipeline() as pipeline:
        input_data = pipeline | "Read Input" >> ReadLocalCSV(beam_input.data_path)
        collections = {INPUT_NODE: input_data}

        output, _ = build_pipeline(pipeline, collections, sorted_nodes)
        output | "Print" >> beam.Map(print)
