import json
import os

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline as BeamPipeline
from apache_beam.pvalue import AsSingleton, PCollection

from vulkan.core.policy import Policy
from vulkan.runners.beam.context import make_beam_context
from vulkan.runners.beam.io import ReadParquet, WriteParquet
from vulkan.runners.beam.nodes import (
    BeamDataInput,
    BeamInput,
    BeamLogicNode,
    BeamNode,
    to_beam_node,
)
from vulkan.schemas import DataSourceSpec
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.graph import GraphEdges, GraphNodes, sort_nodes
from vulkan.spec.nodes.base import NodeType

LOCAL_RESULTS_FILE_NAME = "output.json"


class BeamPipelineBuilder:
    def __init__(
        self,
        policy: Policy,
        output_path: str,
        data_sources: dict[str, DataSourceSpec] | None,
        config_variables: dict[str, str],
    ):
        self.nodes: GraphNodes = policy.nodes
        self.edges: GraphEdges = policy.edges
        self._validate_nodes()

        self.output_path = output_path
        self.data_sources = data_sources
        self.config_variables = config_variables
        self.context = make_beam_context(config_variables)

    def build_batch_pipeline(
        self,
        input_data_path: str,
        backfill_id: str,
        pipeline_options: PipelineOptions | None = None,
    ) -> BeamPipeline:
        if not pipeline_options:
            pipeline_options = PipelineOptions()

        # TODO: We may want to save the input schema instead of creating this node.
        #       This would allow us to create the input collection and output schema directly.
        for node in self.nodes:
            if node.type == NodeType.INPUT and node.hierarchy is None:
                input_node = BeamInput.from_spec(
                    node,
                    data_path=input_data_path,
                )

        sorted_nodes = self._make_sorted_beam_nodes()

        pipeline = beam.Pipeline(options=pipeline_options)

        # Create the input PCollection and the collections map
        input_data = pipeline | "Read Input" >> ReadParquet(data_path=input_data_path)
        collections = {INPUT_NODE: input_data}

        # Build the nodes into the pipeline
        result, metadata = build_pipeline(pipeline, collections, sorted_nodes)

        # TODO: We should resolve this schema inside of the Write transform
        output_schema = _make_output_schema(input_node.id, input_node.schema)
        output_prefix = self.output_path + "/output"

        # Write the output to a Parquet file
        result | "Write Output" >> WriteParquet(
            output_prefix, output_schema, backfill_id
        )

        return pipeline

    def build_single_run_pipeline(
        self,
        input_data: dict,
        pipeline_options: PipelineOptions | None = None,
    ) -> BeamPipeline:
        if not pipeline_options:
            pipeline_options = PipelineOptions()

        sorted_nodes = self._make_sorted_beam_nodes()

        pipeline = beam.Pipeline(options=pipeline_options)

        # Create the input PCollection and the collections map
        input_coll = pipeline | "Create Input Collection" >> beam.Create(
            [("sample_data", input_data)]
        )
        collections = {INPUT_NODE: input_coll}

        # Build the nodes into the pipeline
        result, metadata = build_pipeline(pipeline, collections, sorted_nodes)

        # Write the output to a JSON file
        output_path = os.path.join(self.output_path, LOCAL_RESULTS_FILE_NAME)
        (
            result
            | "To JSON" >> beam.Map(lambda r: json.dumps(r))
            | "Write to file"
            >> beam.io.WriteToText(
                output_path,
                num_shards=1,
                shard_name_template="",
            )
        )

        for step, pcoll in metadata.items():
            metadata_path = os.path.join(self.output_path, f"{step}_metadata.json")
            (
                pcoll
                | f"Format Metadata: {step}" >> beam.Map(lambda r: json.dumps(r))
                | f"Write Metadata: {step}"
                >> beam.io.WriteToText(
                    metadata_path,
                    num_shards=1,
                    shard_name_template="",
                )
            )

        return pipeline

    def _make_sorted_beam_nodes(self) -> list[BeamNode]:
        nodes = []
        for node in self.nodes:
            if node.type == NodeType.INPUT and node.hierarchy is None:
                continue

            if node.type == NodeType.DATA_INPUT:
                source_spec = self.data_sources[node.data_source]
                node = BeamDataInput.from_spec(node, source_spec)
                node = node.with_context(self.context)
            else:
                node = to_beam_node(node)
                if isinstance(node, BeamLogicNode):
                    node = node.with_context(self.context)
            nodes.append(node)

        return sort_nodes(nodes, self.edges)

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
        self.metadata = {}

    def build(self, sorted_nodes: list[BeamNode]):
        """Build a Beam pipeline from a list of BeamNodes"""
        # Iteratively update the collections map
        for node in sorted_nodes:
            pcoll = self.get_input_collection(node)
            self.__build_step(pcoll, node)

        # Join terminate nodes into a single output
        leaves = [
            self.collections[node.id]
            for node in sorted_nodes
            # TODO: replace with actual leaves method
            if node.type == NodeType.TERMINATE and not node.hierarchy
        ]
        statuses = leaves | "Join Terminate Nodes" >> beam.Flatten()
        result = {
            INPUT_NODE: self.collections[INPUT_NODE],
            "result": statuses,
        } | "Group Results" >> beam.CoGroupByKey()
        return result, self.metadata

    def get_input_collection(self, node: BeamNode) -> PCollection:
        """Get the input PCollection for a BeamNode operation"""
        if not node.dependencies:
            return self.pipeline

        deps = {
            str(dep): self._make_dependency_collection(dep)
            for dep in node.dependencies.values()
        }

        return deps | f"Join Deps: {node.id}" >> beam.CoGroupByKey()

    def _make_dependency_collection(self, dep: Dependency) -> PCollection:
        if dep.key is None:
            return self.collections[str(dep)]
        coll = self.collections[
            dep.node
        ] | f"Column [{dep.key}] from [{dep.node}]" >> beam.Map(
            lambda x: (x[0], x[1][dep.key])
        )
        return coll

    def __build_step(self, pcoll: PCollection, node: BeamNode) -> None:
        if node.type == NodeType.TRANSFORM:
            output = pcoll | f"Transform: {node.id}" >> node.op()
            self.collections[node.id] = output

        elif node.type == NodeType.TERMINATE:
            output = pcoll | f"Terminate: {node.id}" >> node.op()
            self.collections[node.id] = output

        elif node.type == NodeType.DATA_INPUT:
            output = pcoll | f"Data Input: {node.id}" >> node.op()
            self.collections[node.id] = output.data
            self.metadata[node.id] = output.metadata

        elif node.type == NodeType.BRANCH:
            output = pcoll | f"Branch: {node.id}" >> node.op()

            for output_name in node.choices:
                branch_name = f"{node.id}.{output_name}"
                filter_value = (
                    self.pipeline
                    | f"[{branch_name}] Create Filter Value: {output_name}"
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

        else:
            raise NotImplementedError(f"Node type: {node.type.value}")
