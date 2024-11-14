from dataclasses import dataclass

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline as BeamPipeline
from apache_beam.pvalue import AsSingleton, PCollection
from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import (
    InputNode,
    NodeType,
)

from vulkan.beam.io import ReadParquet, WriteParquet
from vulkan.beam.nodes import BeamInput, BeamNode, BeamLogicNode, to_beam_node
from vulkan.beam.context import make_beam_context
from vulkan.core.graph import GraphEdges, GraphNodes, sort_nodes
from vulkan.core.policy import Policy


@dataclass
class DataEntryConfig:
    source: str
    schema: dict[str, type] | None = None


class BeamPipelineBuilder:
    def __init__(
        self,
        policy: Policy,
        output_path: str,
        data_sources: dict[str, DataEntryConfig],
        config_variables: dict[str, str] = {},
        pipeline_options: PipelineOptions | None = None,
    ):
        self.nodes: GraphNodes = policy.flattened_nodes
        self.edges: GraphEdges = policy.flattened_dependencies
        self._validate_nodes()

        self.output_path = output_path
        self.data_sources = data_sources
        self.context = make_beam_context(config_variables)

        self.pipeline_options = pipeline_options
        if not self.pipeline_options:
            self.pipeline_options = PipelineOptions()

    def build(self) -> BeamPipeline:
        nodes = []

        for node in self.nodes:
            if node.type == NodeType.INPUT:
                input_node = self._make_beam_input(node)
            else:
                node = to_beam_node(node)
                if isinstance(node, BeamLogicNode):
                    node = node.with_context(self.context)
                nodes.append(node)

        sorted_nodes = sort_nodes(nodes, self.edges)
        return self.build_pipeline(input_node, sorted_nodes)

    def build_pipeline(self, input_node, sorted_nodes):
        """Build a Beam pipeline from a list of BeamNodes

        Handles IO steps, reading from and writing to GCS.
        """
        pipeline = beam.Pipeline(options=self.pipeline_options)

        # Create the input PCollection and the collections map
        input_data = pipeline | "Read Input" >> ReadParquet(
            input_node.source, input_node.schema
        )
        collections = {INPUT_NODE: input_data}

        # Build the nodes into the pipeline
        result = build_pipeline(pipeline, collections, sorted_nodes)

        output_schema = {
            "key": str,
            "status": str,
            input_node.name: input_node.schema,
        }
        output_prefix = self.output_path + "/output"

        # Write the output to GCS
        result | "Write Output" >> WriteParquet(output_prefix, output_schema)

        return pipeline

    def _make_beam_input(self, node: InputNode) -> BeamInput:
        source = self.data_sources[INPUT_NODE].source
        return BeamInput.from_spec(node, source=source)

    def _validate_nodes(self):
        for node in self.nodes:
            if node.type not in _IMPLEMENTED_NODETYPES:
                raise ValueError(
                    f"Node type {node.type} is not allowed in a Beam pipeline"
                )


_IMPLEMENTED_NODETYPES = [
    NodeType.INPUT,
    NodeType.BRANCH,
    NodeType.TRANSFORM,
    NodeType.TERMINATE,
]


def build_pipeline(pipeline, collections, sorted_nodes) -> BeamPipeline:
    builder = __PipelineBuilder(pipeline, collections)
    return builder.build(sorted_nodes)


class __PipelineBuilder:
    """Private helper to build steps into a Beam pipeline"""

    def __init__(
        self, pipeline: BeamPipeline, collections: dict[str, PCollection]
    ) -> None:
        self.pipeline = pipeline
        self.collections = collections

    def build(self, sorted_nodes: list[BeamNode]):
        """Build a Beam pipeline from a list of BeamNodes"""
        # Iteratively update the collections map
        for node in sorted_nodes:
            pcoll = self.get_input_collection(node)
            self.__build_step(pcoll, node)

        # Join terminate nodes into a single output
        leaves = [
            self.collections[node.name]
            for node in sorted_nodes
            if node.type == NodeType.TERMINATE
        ]
        statuses = leaves | "Join Terminate Nodes" >> beam.Flatten()
        result = {
            INPUT_NODE: self.collections[INPUT_NODE],
            "result": statuses,
        } | "Group Results" >> beam.CoGroupByKey()
        return result

    def get_input_collection(self, node: BeamNode) -> PCollection:
        """Get the input PCollection for a BeamNode operation"""
        if not node.dependencies:
            return self.pipeline

        dependencies = list(node.dependencies.values())
        if len(dependencies) > 1:
            deps = {str(d): self.collections[str(d)] for d in dependencies}
            return deps | f"Join Deps: {node.name}" >> beam.CoGroupByKey()

        return self.collections[str(dependencies[0])]

    def __build_step(self, pcoll: PCollection, node: BeamNode) -> None:
        if node.type == NodeType.TRANSFORM:
            output = pcoll | f"Transform: {node.name}" >> node.op()
            self.collections[node.name] = output

        elif node.type == NodeType.BRANCH:
            output = pcoll | f"Branch: {node.name}" >> node.op()

            for output_name in node.outputs:
                branch_name = f"{node.name}.{output_name}"
                filter_value = (
                    self.pipeline
                    | f"Create Filter Value: {output_name}"
                    >> beam.Create([output_name])
                )
                self.collections[branch_name] = (
                    output
                    | f"Filter Branch: {branch_name}"
                    >> beam.Filter(
                        lambda x, v: x[1] == v,
                        v=AsSingleton(filter_value),
                    )
                )

        elif node.type == NodeType.TERMINATE:
            output = pcoll | f"Terminate: {node.name}" >> node.op()
            self.collections[node.name] = output

        else:
            raise NotImplementedError(f"Node type: {node.type.value}")
