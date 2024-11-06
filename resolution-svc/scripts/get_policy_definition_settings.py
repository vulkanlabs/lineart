import argparse
import json
import sys

from vulkan_public.exceptions import VulkanInternalException
from vulkan_public.spec.environment.loaders import load_policy_definition

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--file_location", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    try:
        policy_definition = load_policy_definition(args.file_location)
    except VulkanInternalException as e:
        sys.exit(e.exit_status)

    settings = {
        "required_components": [c.alias() for c in policy_definition.components],
        "config_variables": policy_definition.config_variables,
    }

    with open(args.output_file, "w") as f:
        json.dump(settings, f)
