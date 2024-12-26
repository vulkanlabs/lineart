from dataclasses import dataclass

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline as BeamPipeline
from apache_beam.pvalue import AsSingleton, PCollection
from vulkan_public.schemas import DataSourceSpec
from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import InputNode, NodeType

from vulkan.beam.context import make_beam_context
from vulkan.beam.io import ReadParquet, WriteParquet
from vulkan.beam.nodes import (
    BeamDataInput,
    BeamInput,
    BeamLogicNode,
    BeamNode,
    to_beam_node,
)
from vulkan.core.graph import GraphEdges, GraphNodes, sort_nodes
from vulkan.core.policy import Policy


@dataclass
class DataEntryConfig:
    source: str
    spec: DataSourceSpec


class BeamPipelineBuilder:
    def __init__(
        self,
        policy: Policy,
        output_path: str,
        data_sources: dict[str, DataEntryConfig],
        config_variables: dict[str, str] = {},
    ):
        self.nodes: GraphNodes = policy.flattened_nodes
        self.edges: GraphEdges = policy.flattened_dependencies
        self._validate_nodes()

        self.output_path = output_path
        self.data_sources = data_sources
        self.config_variables = config_variables
        self.context = make_beam_context(config_variables)

    def build(
        self,
        backfill_id: str,
        pipeline_options: PipelineOptions | None = None,
    ) -> BeamPipeline:
        if not pipeline_options:
            pipeline_options = PipelineOptions()
        nodes = []

        for node in self.nodes:
            if node.type == NodeType.INPUT:
                input_node = self._make_beam_input(node)
                continue

            node = to_beam_node(node, data_sources=self.data_sources)
            if isinstance(node, (BeamLogicNode, BeamDataInput)):
                node = node.with_context(self.context)
            nodes.append(node)

        sorted_nodes = sort_nodes(nodes, self.edges)
        return self._build_pipeline(
            input_node,
            sorted_nodes,
            backfill_id,
            pipeline_options,
        )

    def _build_pipeline(
        self,
        input_node: BeamInput,
        sorted_nodes: list[BeamNode],
        backfill_id: str,
        pipeline_options: PipelineOptions,
    ):
        """Build a Beam pipeline from a list of BeamNodes

        Handles IO steps, reading from and writing to GCS.
        """
        pipeline = beam.Pipeline(options=pipeline_options)

        # Create the input PCollection and the collections map
        input_data = pipeline | "Read Input" >> ReadParquet(input_node.spec)
        collections = {INPUT_NODE: input_data}

        # Build the nodes into the pipeline
        result = build_pipeline(pipeline, collections, sorted_nodes)

        # TODO: We should resolve this schema inside of the Write transform
        output_schema = _make_output_schema(input_node.name, input_node.schema)
        output_prefix = self.output_path + "/output"

        # Write the output to GCS
        result | "Write Output" >> WriteParquet(
            output_prefix, output_schema, backfill_id
        )

        return pipeline

    def _make_beam_input(self, node: InputNode) -> BeamInput:
        input_source = self.data_sources[INPUT_NODE]
        return BeamInput.from_spec(
            node,
            source=input_source.source,
            spec=input_source.spec,
        )

    def _validate_nodes(self):
        for node in self.nodes:
            if node.type not in _IMPLEMENTED_NODETYPES:
                raise ValueError(
                    f"Node type {node.type} is not allowed in a Beam pipeline"
                )


def _make_output_schema(
    input_node_name: str, input_node_schema: dict[str, type]
) -> dict[str, type]:
    return {
        "backfill_id": str,
        "key": str,
        "status": str,
        input_node_name: input_node_schema,
    }


_IMPLEMENTED_NODETYPES = [
    NodeType.INPUT,
    NodeType.BRANCH,
    NodeType.TRANSFORM,
    NodeType.TERMINATE,
    NodeType.DATA_INPUT,
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
        if len(dependencies) == 1:
            return self.collections[str(dependencies[0])]

        deps = {str(d): self.collections[str(d)] for d in dependencies}
        return deps | f"Join Deps: {node.name}" >> beam.CoGroupByKey()

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

        elif node.type == NodeType.DATA_INPUT:
            output = pcoll | f"Data Input: {node.name}" >> node.op()
            self.collections[node.name] = output

        else:
            raise NotImplementedError(f"Node type: {node.type.value}")
