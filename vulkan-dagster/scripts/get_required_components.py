import argparse
import json
import sys

from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan.environment.loaders import load_policy_definition


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    try:
        policy_definition = load_policy_definition(args.file_location)
    except Exception as e:
        sys.exit(3)

    required_components = {
        "required_components": [c.alias() for c in policy_definition.components]
    }

    with open(args.output_file, "w") as f:
        json.dump(required_components, f, cls=EnhancedJSONEncoder)
