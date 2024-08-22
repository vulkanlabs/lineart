import importlib.util
import json
import sys

from vulkan_dagster.core.nodes import NodeType
from vulkan_dagster.dagster.policy import DagsterPolicy

import dataclasses

class EnhancedJSONEncoder(json.JSONEncoder):
        def default(self, o):
            if dataclasses.is_dataclass(o):
                return dataclasses.asdict(o)
            return super().default(o)

file_location = f"{sys.argv[1]}/__init__.py"
temp_location = sys.argv[2]

spec = importlib.util.spec_from_file_location("user.policy", file_location)
module = importlib.util.module_from_spec(spec)
sys.modules["user.policy"] = module
spec.loader.exec_module(module)

context = vars(module)
print(context)



# TODO: This function should come from the core library
def _to_dict(node):
    node_ = node.__dict__.copy()
    if node.node_type == NodeType.COMPONENT.value:
        node_["metadata"]["nodes"] = {
            name: _to_dict(n) for name, n in node.metadata["nodes"].items()
        }
    return node_


for _, obj in context.items():
    if isinstance(obj, DagsterPolicy):
        nodes = {name: _to_dict(node) for name, node in obj.node_definitions.items()}
        with open(temp_location, "w") as f:
            json.dump(nodes, f, cls=EnhancedJSONEncoder)
        break
