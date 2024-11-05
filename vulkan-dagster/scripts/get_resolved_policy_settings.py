import argparse
import json

from vulkan.core.graph import extract_node_definitions
from vulkan.environment.loaders import resolve_policy
from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan_public.spec.nodes import NodeType


def _extract_data_sources(nodes):
    return [n.source for n in nodes if n.type == NodeType.DATA_INPUT]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    resolved_policy = resolve_policy(args.file_location, args.components_base_dir)

    nodes = extract_node_definitions(resolved_policy.nodes)
    data_sources = _extract_data_sources(resolved_policy.flattened_nodes)
    settings = {"nodes": nodes, "data_sources": data_sources}

    with open(args.output_file, "w") as f:
        json.dump(settings, f, cls=EnhancedJSONEncoder)
