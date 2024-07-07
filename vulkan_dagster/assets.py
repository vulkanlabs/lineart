
from dagster import Definitions, GraphDefinition, asset
from vulkan_dagster.nodes import HTTPConnection, HTTPConnectionConfig, NodeType, Context, NodeConfig, Transform

context = Context(
    data={
        "cpf": "12345678900"
    },
    variables={}
)

config = HTTPConnectionConfig(
    name="scr",
    description="Get SCR score",
    type=NodeType.CONNECTION,
    url="http://127.0.0.1:5000",
    method="GET",
    headers={},
    params={},
) 
n1 = HTTPConnection(config)

config = NodeConfig(
    name="transform",
    description="Transform data",
    type=NodeType.TRANSFORM,
)

# The function has to specify a set of parameters that is defined in other assets.
def f2(context, scr_response):
    context.log.info(f"Received SCR: {scr_response}")
    score = scr_response["score"]
    return score * 2

p2 = {"scr_response": "scr"}
n2 = Transform(config, f2, p2)

vulkan_nodes = [n1, n2]

dagster_nodes = []
deps = {}
for n in vulkan_nodes:
    node, node_deps = n.node()
    dagster_nodes.append(node)
    if node_deps is not None:
        deps[n.config.name] = node_deps
        # {"transform": {"scr_response": ("scr", "result")}}

graph = GraphDefinition(
    name="policy",
    description="Policy graph",
    node_defs=dagster_nodes,
    dependencies=deps,
)
job = graph.to_job(name="policy_job")

@asset
def hello_world():
    return "Hello, world!"

definitions = Definitions(
    jobs=[job],
)

print(definitions.jobs[0].name)
