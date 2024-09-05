import argparse
import json

from vulkan.core.policy import extract_node_definitions
from vulkan.dagster.workspace import resolve_policy
from vulkan.environment.encoders import EnhancedJSONEncoder


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    resolved_policy = resolve_policy(args.file_location, args.components_base_dir)
    nodes = extract_node_definitions(resolved_policy)

    with open(args.output_file, "w") as f:
        json.dump(nodes, f, cls=EnhancedJSONEncoder)
