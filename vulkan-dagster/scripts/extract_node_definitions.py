import argparse
import dataclasses
import json

from vulkan.core.nodes import NodeType
from vulkan.dagster.workspace import resolve_policy


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o):
        if dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        return super().default(o)


# TODO: This function should come from the core library
def _to_dict(node):
    node_ = node.__dict__.copy()
    if node.node_type == NodeType.COMPONENT.value:
        node_["metadata"]["nodes"] = {
            name: _to_dict(n) for name, n in node.metadata["nodes"].items()
        }
    return node_


def extract_node_definitions(file_location, components_base_dir):
    resolved_policy = resolve_policy(file_location, components_base_dir)

    nodes = {
        node.name: _to_dict(node.node_definition()) 
        for node 
        in resolved_policy.nodes
    }
    return nodes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    nodes = extract_node_definitions(args.file_location, args.components_base_dir)
    with open(args.output_file, "w") as f:
        json.dump(nodes, f, cls=EnhancedJSONEncoder)
