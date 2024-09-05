import argparse
import json

from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan.environment.loaders import load_component_definition_from_alias

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    component_definition = load_component_definition_from_alias(
        args.alias, args.components_base_dir
    )
    config = dict(
        input_schema=component_definition.input_schema,
        instance_params_schema=component_definition.instance_params_schema,
    )

    with open(args.output_file, "w") as f:
        json.dump(config, f, cls=EnhancedJSONEncoder)
