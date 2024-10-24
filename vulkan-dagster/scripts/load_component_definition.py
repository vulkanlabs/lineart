import argparse
import json
import sys

from vulkan.core.graph import extract_node_definitions
from vulkan.environment.encoders import EnhancedJSONEncoder
from vulkan_public.exceptions import VulkanInternalException
from vulkan_public.spec.environment.loaders import load_component_definition_from_alias
from vulkan_public.spec.nodes import NodeType


def _extract_data_sources(nodes):
    return [n.source for n in nodes if n.type == NodeType.DATA_INPUT]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--alias", type=str)
    parser.add_argument("--components_base_dir", type=str)
    parser.add_argument("--output_file", type=str)
    args = parser.parse_args()

    try:
        component = load_component_definition_from_alias(
            args.alias, args.components_base_dir
        )
    except VulkanInternalException as e:
        sys.exit(e.exit_status)

    config = dict(
        input_schema=component.input_schema,
        instance_params_schema=component.instance_params_schema,
        node_definitions=extract_node_definitions(component.nodes),
        data_sources=_extract_data_sources(component.nodes),
    )

    with open(args.output_file, "w") as f:
        json.dump(config, f, cls=EnhancedJSONEncoder)
