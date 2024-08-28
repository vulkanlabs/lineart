import argparse
import dataclasses
import importlib.util
import json
import os
import sys

from vulkan.core.nodes import NodeType
from vulkan.dagster.policy import DagsterPolicy


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
    if not os.path.exists(file_location):
        raise ValueError(f"File not found: {file_location}")

    spec = importlib.util.spec_from_file_location("user.policy", file_location)
    module = importlib.util.module_from_spec(spec)
    sys.modules["user.policy"] = module
    spec.loader.exec_module(module)

    context = vars(module)

    for _, obj in context.items():
        if isinstance(obj, DagsterPolicy):
            nodes = {
                name: _to_dict(node) for name, node in obj.node_definitions.items()
            }
            return nodes
    raise ValueError("No policy definition found in module")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    nodes = extract_node_definitions(args.file_location)
    with open(args.output_file, "w") as f:
        json.dump(nodes, f, cls=EnhancedJSONEncoder)
