from json import loads

from vulkan_public.spec.component import ComponentDefinition, InstanceParam
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes import HTTPConnectionNode, TransformNode


def serasa_func(context, serasa_response, **kwargs):
    data = loads(serasa_response)
    context.log.info(f"Received Serasa: {data}")
    score = 2 * data["score"] ** -1
    context.log.warning(f"Transformed Serasa: {score}")
    return score


body = TransformNode(
    func=lambda inputs: {"tax_id": inputs["cpf"]},
    name="body",
    description="Serasa body",
    dependencies={"inputs": Dependency(INPUT_NODE)},
)

query = HTTPConnectionNode(
    name="query",
    description="Get Serasa score",
    url=InstanceParam("server_url"),
    method="GET",
    headers={},
    params={},
    dependencies={"body": Dependency("body")},
)

transform = TransformNode(
    func=serasa_func,
    name="transform",
    description="Transform sample Serasa data",
    dependencies={"serasa_response": Dependency("query")},
)


test_component = ComponentDefinition(
    nodes=[body, query, transform],
    input_schema={"cpf": str},
    instance_params_schema={"server_url": str},
)
