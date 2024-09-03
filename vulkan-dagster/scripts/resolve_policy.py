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


def extract_node_definitions(policy):
    nodes = {
        node.name: _to_dict(node.node_definition()) 
        for node 
        in policy.nodes
    }
    return nodes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    resolved_policy = resolve_policy(args.file_location, args.components_base_dir)
    required_components = [c.reference for c in resolved_policy.components]
    nodes = extract_node_definitions(resolved_policy)
    result = {
        "nodes": nodes,
        "required_components": required_components
    }

    with open(args.output_file, "w") as f:
        json.dump(result, f, cls=EnhancedJSONEncoder)
