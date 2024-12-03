import json

from vulkan_public.spec.component import ComponentDefinition
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import DataInputNode, TransformNode

body = TransformNode(
    func=lambda inputs: {"tax_id": inputs["cpf"]},
    name="body",
    description="Serasa body",
    dependencies={"inputs": Dependency(INPUT_NODE)},
)

get_data = DataInputNode(
    name="vendor_api_data",
    description="Get data from Vendor API",
    source="vendor-name:api-name:v0.0.1",
    dependencies={"body": Dependency(body.name)},
)


def load_data(context, raw_data, **kwargs):
    context.log.info(f"Raw data: {raw_data}")
    data = json.loads(raw_data)
    context.log.info(f"Data loaded: {data} ({type(data)})")
    return data


process_data = TransformNode(
    func=load_data,
    name="post_process_data",
    description="Post process data",
    dependencies={"raw_data": Dependency(get_data.name)},
)

vendor_data_source_example = ComponentDefinition(
    nodes=[body, get_data, process_data],
    input_schema={"cpf": str},
)
