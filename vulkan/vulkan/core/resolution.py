from copy import deepcopy

from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import (
    InputNode,
    Node,
    NodeType,
    TerminateNode,
    TransformNode,
)
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

    # For each component, we resolve the component and then insert all
    # its nodes into the flattened node list.
    for node in component_nodes:
        if node.definition is None:
            msg = f"Component node {node.id} has no definition"
            raise ValueError(msg)

        hierarchy = (node.hierarchy or []) + [node.name]
        component = PolicyDefinition.from_dict(node.definition, hierarchy=hierarchy)
        component_nodes = {n.id: n for n in component.nodes}

        # Inject the component's dependencies into the input node
        # and replace the input node with an identity transform node.
        input_node = component.input_node.with_dependencies(node.dependencies)
        input_node = _identity_transform_from_input_node(input_node, node.parameters)
        component_nodes[input_node.id] = input_node

        # Replace the leaves (terminates) with identity transform nodes.
        leaves = {
            leaf.id: _identity_transform_from_terminate_node(leaf)
            for leaf in component.leaves.values()
        }
        component_nodes.update(leaves)

        # Join workflow outputs into an identity transform node
        output_joiner = _make_output_joiner(
            subpolicy_name=node.name,
            leaves=leaves,
            hierarchy=node.hierarchy,
        )
        component_nodes[output_joiner.id] = output_joiner

        # Add nodes in the component to the node map
        node_map.update(component_nodes)

    return list(node_map.values())


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
        name=subpolicy_name,
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


def _identity_transform_from_input_node(
    input_node: InputNode,
    parameters: dict[str, str],
) -> TransformNode:
    return TransformNode(
        name=input_node.name,
        func=_identity_transform(input_node.schema),
        dependencies=input_node.dependencies,
        description=input_node.description,
        hierarchy=input_node.hierarchy,
        parameters=parameters,
    )


def _identity_transform_from_terminate_node(node: TerminateNode) -> TransformNode:
    parameters = node.output_data or {}
    parameters["return_status"] = node.return_status
    return TransformNode(
        name=node.name,
        func=_identity_fn,
        dependencies=node.dependencies,
        description=node.description,
        hierarchy=node.hierarchy,
        parameters=parameters,
    )


def _identity_fn(**kwargs):
    if len(kwargs) == 1:
        return list(kwargs.values())[0]
    return kwargs


def _identity_transform(input_schema: dict[str, type]):
    def _identity(**kwargs):
        if len(kwargs) == 1:
            return list(kwargs.values())[0]
        with_types = deepcopy(kwargs)
        for k, typ in input_schema.items():
            # If the key is in the input schema, we need to cast the value to the type.
            if k in with_types:
                with_types[k] = typ(with_types[k])
        return with_types

    return _identity
