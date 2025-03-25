from json import loads

from vulkan_public.spec.component import ComponentDefinition, InstanceParam
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import HTTPConnectionNode, TransformNode


# The user function needs to use a set of parameters
# that is defined by previous ops (validated in dagster).
# It also needs to take the context and **kwargs.
def scr_func(context, scr_response, **kwargs):
    data = loads(scr_response)
    context.log.info(f"Received SCR: {data}")
    score = data["score"]
    return score


body = TransformNode(
    func=lambda inputs: {"tax_id": inputs["cpf"]},
    name="body",
    description="SCR body",
    # User has to point to the Component's input node, named INPUT_NODE
    dependencies={"inputs": Dependency(INPUT_NODE)},
)

scr_query = HTTPConnectionNode(
    name="query",
    description="Get SCR score",
    method="GET",
    headers={},
    params={},
    dependencies={"body": Dependency("body")},
    url=InstanceParam("server_url"),
)

scr_transform = TransformNode(
    func=scr_func,
    name="transform",
    description="Transform SCR data",
    dependencies={"scr_response": Dependency("query")},
)

test_component = ComponentDefinition(
    nodes=[body, scr_query, scr_transform],
    input_schema={"cpf": str},
    instance_params_schema={"server_url": str},
)
