import importlib.util
import json
import sys

from vulkan_dagster.policy import Policy

file_location = f"{sys.argv[1]}/__init__.py"
temp_location = sys.argv[2]

spec = importlib.util.spec_from_file_location("user.policy", file_location)
module = importlib.util.module_from_spec(spec)
sys.modules["user.policy"] = module
spec.loader.exec_module(module)

context = vars(module)
print(context)

for _, obj in context.items():
    if isinstance(obj, Policy):
        nodes = {name: node.__dict__ for name, node in obj.node_definitions().items()}
        with open(temp_location, "w") as f:
            json.dump(nodes, f)
        break
