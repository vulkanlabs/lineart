import argparse
import json

from vulkan.core.graph import extract_node_definitions
from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan.environment.loaders import load_component_definition_from_alias


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    component = load_component_definition_from_alias(
        args.alias, args.components_base_dir
    )
    config = dict(
        input_schema=component.input_schema,
        instance_params_schema=component.instance_params_schema,
        node_definitions=extract_node_definitions(component.nodes),
    )

    with open(args.output_file, "w") as f:
        json.dump(config, f, cls=EnhancedJSONEncoder)
