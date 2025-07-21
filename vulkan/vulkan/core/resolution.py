from copy import deepcopy

from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import InputNode, Node, NodeType, TransformNode
from vulkan.spec.policy import PolicyDefinition


def resolve(
    nodes: list[Node],
) -> list[Node]:
    """Resolve a Policy Definition into a Policy.
    The resolution consists of a couple of things:
    1. Resolve any component node into their corresponding workflow;
    2. Join the outputs of each component into a single node;
    3. Remove the component nodes from the list of nodes;
    4. Update the dependencies for nodes that depend on components.
    """
    component_nodes = [node for node in nodes if node.type == NodeType.COMPONENT]
    # There is nothing to resolve if there are no nested flows (ie. components).
    if len(component_nodes) == 0:
        return nodes

    node_map = {node.id: node for node in nodes if node.type != NodeType.COMPONENT}
    resolved = []
    replacement_dependencies = {}

    component_node_ids = set(node.id for node in component_nodes)

    # For each component, we resolve the component and then insert all
    # its nodes into the flattened node list.
    for node in component_nodes:
        if node.definition is None:
            msg = f"Component node {node.id} has no definition"
            raise ValueError(msg)

        hierarchy = (node.hierarchy or []) + [node.name]
        component = PolicyDefinition.from_dict(node.definition, hierarchy=hierarchy)

        # Inject the component's dependencies into the input node
        component.input_node = component.input_node.with_dependencies(node.dependencies)

        # Join workflow outputs into an identity transform node
        output_joiner = _make_output_joiner(
            subpolicy_name=node.id,
            leaves=component.leaves,
            hierarchy=hierarchy,
        )
        component.nodes.append(output_joiner)
        replacement_dependencies[node.id] = Dependency(
            output_joiner.name,
            hierarchy=hierarchy,
        )

        # Add nodes in the component to the node map
        for n in component.nodes:
            node_map[n.id] = n

    for _node in node_map.values():
        # If a node doesn't depend on any component, it's already resolved.
        deps = set((n.id for n in _node.dependencies.values()))
        intersection = set(component_node_ids) & deps
        if len(intersection) == 0:
            resolved.append(_node)
            continue

        if _node.type == NodeType.COMPONENT:
            # Components aren't handled in the actual computation.
            # They're not added to the resolved list.
            continue

        # Avoid modifying the original node
        node = deepcopy(_node)
        original_dependencies = deepcopy(node.dependencies)

        # Reassign dependencies on nested workflows.
        # If a node depends on a component, it'll instead depend
        # on the output joiner of that component.
        for dep_name, dependency in original_dependencies.items():
            replacement = replacement_dependencies.get(dependency.id)
            if replacement is None:
                continue
            node.dependencies[dep_name] = replacement

        resolved.append(node)

    return resolved


def _make_output_joiner(
    subpolicy_name: str,
    leaves: dict[str, Node],
    hierarchy: list[str] | None,
) -> TransformNode:
    description = f"Inserted automatically to join the outputs of {subpolicy_name}"
    dependencies = {
        name: Dependency(leaf.name, hierarchy=leaf.hierarchy)
        for name, leaf in leaves.items()
    }
    return TransformNode(
        name=f"{subpolicy_name}_joiner",
        func=_or_op_leaves,
        dependencies=dependencies,
        description=description,
        hierarchy=hierarchy,
    )


def _or_op_leaves(**kwargs):
    non_null_count = 0
    retval = None
    for value in kwargs.values():
        if value is not None:
            non_null_count += 1
            retval = value

    if non_null_count != 1:
        msg = f"Exactly one leaf should execute, got {non_null_count=}"
        raise ValueError(msg)
    return retval
