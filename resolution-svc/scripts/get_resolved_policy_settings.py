import argparse
import json

from vulkan.core.graph import extract_node_definitions
from vulkan.environment.loaders import resolve_policy
from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan_public.spec.nodes import NodeType


def _extract_data_sources(nodes):
    return [n.source for n in nodes if n.type == NodeType.DATA_INPUT]


def _extract_input_schema(nodes):
    input_node = [n for n in nodes if n.type == NodeType.INPUT][0]
    return input_node.schema


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--module_name", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    resolved_policy = resolve_policy(args.module_name, args.components_base_dir)

    nodes = extract_node_definitions(resolved_policy.nodes)
    input_schema = _extract_input_schema(resolved_policy.nodes)
    data_sources = _extract_data_sources(resolved_policy.flattened_nodes)
    settings = {
        "nodes": nodes,
        "input_schema": input_schema,
        "data_sources": data_sources,
    }

    with open(args.output_file, "w") as f:
        # We need to use the EnhancedJSONEncoder to serialize the types
        # in `input_schema`
        json.dump(settings, f, cls=EnhancedJSONEncoder)
