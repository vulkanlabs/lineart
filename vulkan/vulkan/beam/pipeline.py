import hashlib
import json
from dataclasses import dataclass
from functools import partial

import apache_beam as beam
from apache_beam.dataframe import convert
from apache_beam.dataframe.io import read_csv
from apache_beam.options.pipeline_options import PipelineOptions
from apache_beam.pipeline import Pipeline as BeamPipeline
from apache_beam.pvalue import AsSingleton, PCollection
from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import (
    InputNode,
    NodeType,
)
import csv

from vulkan.beam.nodes import BeamInput, BeamNode, to_beam_node
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
        data_sources: dict[str, DataEntryConfig],
        config_variables: dict[str, str] = {},
        pipeline_options: PipelineOptions | None = None,
    ):
        # validate the input schema (all rows must be either python pure types
        # or convertible to python pure types)
        # Check IO nodes' schemas
        self.nodes: GraphNodes = policy.flattened_nodes
        self.edges: GraphEdges = policy.flattened_dependencies
        self._validate_nodes()

        self.data_sources = data_sources
        self.config_variables = config_variables

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
                if node.type in _CONFIGURABLE_NODETYPES:
                    node = node.with_env(self.config_variables)
                nodes.append(node)

        sorted_nodes = sort_nodes(nodes, self.edges)

        pipeline = beam.Pipeline(options=self.pipeline_options)
        return build_pipeline(pipeline, input_node, sorted_nodes)

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
_CONFIGURABLE_NODETYPES = [NodeType.BRANCH, NodeType.TRANSFORM]


def build_pipeline(pipeline, input_node, sorted_nodes) -> BeamPipeline:
    """Build a Beam pipeline from a list of BeamNodes

    Handles IO steps, reading and writing data to/from GCS.
    """
    # TODO: get read options from config
    input_data = pipeline | "Read Input" >> ReadGCSInput(
        input_node.source, input_node.schema
    )
    collections = {INPUT_NODE: input_data}

    builder = __PipelineBuilder(pipeline, collections)
    result = builder.build(sorted_nodes)

    # TODO: write result to GCS
    result | "Write Output" >> beam.io.WriteToText("gs://vulkan-dev-temp/output.txt")

    return builder.pipeline


def build_local_pipeline(pipeline, input_node, sorted_nodes):
    """For testing purposes, build a pipeline that reads from a local file"""
    input_data = pipeline | "Read Input" >> ReadLocalInput(input_node.source)
    collections = {INPUT_NODE: input_data}

    builder = __PipelineBuilder(pipeline, collections)
    return builder.build(sorted_nodes)


class ReadGCSInput(beam.PTransform):
    def __init__(self, source: str, schema: dict[str, type] | None = None):
        self.source = source

        fields = list(schema.keys())
        self.csv_parser = partial(parse_csv_line, fields=fields)

    def expand(self, pcoll):
        return (
            pcoll
            | "Read From GCS" >> beam.io.ReadFromText(self.source, skip_header_lines=1)
            | "Parse CSV" >> beam.Map(self.csv_parser)
            | "Make Key" >> beam.Map(_make_element_key)
        )


def parse_csv_line(fields, line):
    """Parse a single line of CSV into a dictionary."""
    reader = csv.reader([line])
    return dict(zip(fields, next(reader)))


class ReadLocalInput(beam.PTransform):
    def __init__(self, source: str):
        self.source = source

    def expand(self, pcoll):
        dataframe = pcoll | "Read Source" >> read_csv(self.source)
        return (
            convert.to_pcollection(dataframe)
            | "To dictionaries" >> beam.Map(lambda x: dict(x._asdict()))
            | "Make Key" >> beam.Map(_make_element_key)
        )


def _make_element_key(element: dict) -> tuple[str, dict]:
    content = json.dumps(element, sort_keys=True)
    key = hashlib.md5(content.encode("utf-8")).hexdigest()
    return (key, element)


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
