import apache_beam as beam
import numpy as np
from apache_beam.testing.test_pipeline import TestPipeline
from apache_beam.testing.util import assert_that, equal_to
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import BranchNode, NodeType, TerminateNode, TransformNode

from vulkan.beam.io import (
    ReadLocalCSV,
)
from vulkan.beam.nodes import (
    BeamBranch,
    BeamInput,
    BeamTerminate,
    BeamTransform,
    to_beam_nodes,
)
from vulkan.beam.pipeline import build_pipeline
from vulkan.core.graph import sort_nodes
from vulkan.core.policy import Policy


def test_beam_transform():
    add_one = BeamTransform(
        name="add_one",
        func=lambda x: x["number"] + 1,
        dependencies={"x": Dependency("input_node")},
    )
    log = BeamTransform(
        name="log",
        func=lambda x: np.log(x) if x > 0 else 0,
        dependencies={"x": Dependency(add_one.name)},
    )
    double = BeamTransform(
        name="double",
        func=lambda x: x * 2,
        dependencies={"x": Dependency(log.name)},
    )
    entries = [(i, {"number": i}) for i in range(1, 5)]

    with TestPipeline() as p:
        inputs = p | beam.Create(entries)
        output = (
            inputs
            | "Add one" >> add_one.op()
            | "Log" >> log.op()
            | "Double" >> double.op()
        )
        output | "Print" >> beam.Map(print)
        assert_that(output, equal_to([(x, np.log((x + 1)) * 2) for x in range(1, 5)]))


def test_pipeline():
    input_node = BeamInput(
        name=INPUT_NODE,
        schema={"number": int},
        source="vulkan/beam/test/input_data.csv",
    )

    def _branch(data):
        if data["score"] > 500:
            return "approved"
        return "denied"

    branch = BeamBranch(
        name="branch",
        func=_branch,
        outputs=["approved", "denied"],
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

    # with beam.Pipeline(
    #     runner=RenderRunner(),
    #     options=beam.options.pipeline_options.PipelineOptions(),
    # ) as p:
    with TestPipeline() as pipeline:
        input_data = pipeline | "Read Input" >> ReadLocalCSV(input_node.source)
        collections = {INPUT_NODE: input_data}

        output = build_pipeline(pipeline, collections, [branch, approved, denied])
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
        outputs=["approved", "denied"],
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

    policy = Policy(
        nodes=[transform, branch, approved, denied],
        input_schema={"data": dict},
    )
    nodes = policy.flattened_nodes
    edges = policy.flattened_dependencies

    input_node = [node for node in nodes if node.type == NodeType.INPUT][0]
    core_nodes = [node for node in nodes if node.type != NodeType.INPUT]

    beam_input = BeamInput.from_spec(
        input_node, source="vulkan/beam/test/input_data.csv"
    )
    beam_nodes = to_beam_nodes(core_nodes)
    sorted_nodes = sort_nodes(beam_nodes, edges)

    with TestPipeline() as pipeline:
        input_data = pipeline | "Read Input" >> ReadLocalCSV(beam_input.source)
        collections = {INPUT_NODE: input_data}

        output = build_pipeline(pipeline, collections, sorted_nodes)
        output | "Print" >> beam.Map(print)
