from dagster import GraphDefinition

from vulkan_dagster.policy import policy_nodes

dagster_nodes = []
deps = {}
for n in policy_nodes:
    node, node_deps = n.node()
    dagster_nodes.append(node)
    if node_deps is not None:
        deps[n.name] = node_deps

graph = GraphDefinition(
    name="policy",
    description="Policy graph",
    node_defs=dagster_nodes,
    dependencies=deps,
)
