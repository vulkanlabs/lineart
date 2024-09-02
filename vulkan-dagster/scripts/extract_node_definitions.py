import argparse
import dataclasses
import importlib.util
import json
import os
import sys

from vulkan.core.nodes import NodeType
from vulkan.core.policy import PolicyDefinition
from vulkan.environment.packing import find_definitions


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


def extract_node_definitions(file_location):
    policies = find_definitions(file_location, PolicyDefinition)
    if len(policies) != 1:
        raise ValueError("Expected exactly one PolicyDefinition definition in the module")

    obj = policies[0]
    nodes = {
        name: _to_dict(node) for name, node in obj.node_definitions.items()
    }
    return nodes


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    nodes = extract_node_definitions(args.file_location)
    with open(args.output_file, "w") as f:
        json.dump(nodes, f, cls=EnhancedJSONEncoder)
