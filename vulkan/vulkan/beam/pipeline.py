import hashlib
import json
from dataclasses import dataclass

import apache_beam as beam
from apache_beam.dataframe.io import read_csv
from apache_beam.dataframe import convert
from vulkan_public.spec.dependency import INPUT_NODE
from vulkan_public.spec.nodes import (
    InputNode,
    NodeType,
)

from vulkan.beam.nodes import BeamInput, BeamNode


def make_element_key(element: dict) -> tuple[str, dict]:
    content = json.dumps(element, sort_keys=True)
    key = hashlib.md5(content.encode("utf-8")).hexdigest()
    return (key, element)


def make_beam_pipeline(input_node, sorted_nodes):
    with beam.Pipeline() as pipeline:
        result = build_pipeline(pipeline, input_node, sorted_nodes)

        # write output to destination
        (result | "Print" >> beam.Map(print))


def build_pipeline(pipeline, input_node, sorted_nodes):
    # TODO: get read options from config
    df = pipeline | "Read Input" >> read_csv(input_node.source)
    input_data = (
        convert.to_pcollection(df)
        | "To dictionaries" >> beam.Map(lambda x: dict(x._asdict()))
        | "Make Key" >> beam.Map(make_element_key)
    )
    collections = {INPUT_NODE: input_data}

    for node in sorted_nodes:
        dependencies = list(node.dependencies.values()) if node.dependencies else []

        if len(dependencies) > 1:
            deps = {str(dep): collections[str(dep)] for dep in dependencies}
            pcoll = deps | f"Join Deps: {node.name}" >> beam.CoGroupByKey()

        elif len(dependencies) == 1:
            pcoll = collections[str(dependencies[0])]

        else:
            pcoll = pipeline

        if node.type == NodeType.TRANSFORM:
            output = pcoll | f"Transform: {node.name}" >> node.op()
            collections[node.name] = output

        elif node.type == NodeType.BRANCH:
            output = pcoll | f"Branch: {node.name}" >> node.op()

            for output_name in node.outputs:
                branch_name = f"{node.name}.{output_name}"
                filter_value = (
                    pipeline
                    | f"Create Filter Value: {output_name}"
                    >> beam.Create([output_name])
                )
                collections[branch_name] = (
                    output
                    | f"Filter Branch: {branch_name}"
                    >> beam.Filter(
                        lambda x, v: x[1] == v, v=beam.pvalue.AsSingleton(filter_value)
                    )
                )

        elif node.type == NodeType.TERMINATE:
            output = pcoll | f"Terminate: {node.name}" >> node.op()
            collections[node.name] = output

    # join terminate nodes into single output
    leaves = [
        collections[node.name]
        for node in sorted_nodes
        if node.type == NodeType.TERMINATE
    ]
    result = leaves | "Join Terminate Nodes" >> beam.Flatten()
    return result
