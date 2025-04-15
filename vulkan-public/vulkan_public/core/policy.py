import builtins
from copy import deepcopy
from typing import Callable

from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.graph import GraphDefinition
from vulkan_public.spec.nodes import (
    InputNode,
    Node,
    NodeType,
    TerminateNode,
    TransformNode,
)
from vulkan_public.spec.policy import PolicyDefinition


class Policy(GraphDefinition):
    def __init__(
        self,
        nodes: list[Node],
        input_schema: dict[str, type | str],
        output_callback: Callable | None = None,
        hierarchy_level: str | None = None,
    ):
        if output_callback is not None:
            if not callable(output_callback):
                msg = "Output callback must be callable (a function or method)"
                raise TypeError(msg)
            nodes = self._with_output_callback(nodes, output_callback)

        input_schema = _parse_input_schema(input_schema)

        all_nodes = [_make_input_node(input_schema), *nodes]
        if hierarchy_level is not None:
            all_nodes = [
                node.add_hierarchy_level(hierarchy_level) for node in all_nodes
            ]

        self.hierarchy_level = hierarchy_level
        self.nodes = resolve(all_nodes)
        self.input_schema = input_schema
        self.output_callback = output_callback
        super().__post_init__()

    def _with_output_callback(
        self, nodes: list[Node], output_callback: Callable
    ) -> list[Node]:
        modified_nodes = []
        for node in nodes:
            if isinstance(node, TerminateNode):
                node = node.with_callback(output_callback)
            modified_nodes.append(node)

        return modified_nodes

    @classmethod
    def from_definition(
        cls,
        definition: PolicyDefinition,
        hierarchy_level: str | None = None,
    ) -> "Policy":
        if not definition.valid:
            msg = f"Policy definition is not valid: {definition.errors}"
            raise ValueError(msg)

        return cls(
            nodes=definition.nodes,
            input_schema=definition.input_schema,
            output_callback=definition.output_callback,
            hierarchy_level=hierarchy_level,
        )


def _parse_input_schema(input_schema: dict[str, type | str]) -> dict[str, type | str]:
    """Parse the input schema to ensure that all types are valid."""
    parsed_schema = {}
    for key, value in input_schema.items():
        if isinstance(value, str):
            # If the type is a string, we assume it's a built-in type
            if hasattr(builtins, value):
                parsed_schema[key] = getattr(builtins, value)
            else:
                msg = f"Invalid type '{value}' for key '{key}'"
                raise ValueError(msg)
        elif isinstance(value, type):
            parsed_schema[key] = value
        else:
            msg = f"Invalid type for key '{key}': {type(value)}"
            raise ValueError(msg)
    return parsed_schema


def _make_input_node(input_schema) -> InputNode:
    return InputNode(
        name=INPUT_NODE,
        description="Input node",
        schema=input_schema,
    )


def resolve(nodes: list[Node]) -> list[Node]:
    """Resolve a Policy Definition into a Policy.
    The resolution step consists of a couple of things:
    1. Resolve any policy definition node into their corresponding policy;
    2. Join the outputs of each subpolicy into a single node;
    3. Remove the subpolicy nodes from the list of nodes;
    4. Update the dependencies for nodes that depend on subpolicies.
    """
    node_map = {node.id: node for node in nodes}
    resolved = []
    replacement_dependencies = {}

    # For each subpolicy, we resolve the subpolicy and then insert all
    # its nodes into the flattened node list.
    for node in nodes:
        if node.type == NodeType.POLICY:
            policy_node = Policy.from_definition(node.policy_definition, node.id)
            # TODO: This should maybe go into the `from_definition` method?
            i, inner_input_node = _find_input_node(policy_node.nodes)
            policy_node.nodes[i] = inner_input_node.with_dependencies(node.dependencies)
            # Join subpolicy outputs into an identity transform node
            output_joiner = _make_output_joiner(
                subpolicy_name=node.id,
                leaves=policy_node.leaves,
                hierarchy=inner_input_node.hierarchy,
            )
            policy_node.nodes.append(output_joiner)
            replacement_dependencies[node.id] = Dependency(
                output_joiner.name,
                hierarchy=inner_input_node.hierarchy,
            )

            for n in policy_node.nodes:
                node_map[n.id] = n

    for _node in node_map.values():
        # Avoid modifying the original node
        node = deepcopy(_node)

        if node.type == NodeType.POLICY:
            # Policies are treated as "virtual" nodes:
            # ie. they exist, but aren't handled in the actual computation.
            # There's no need to modify their dependencies.
            continue

        original_dependencies = deepcopy(node.dependencies)
        for dep_name, dependency in original_dependencies.items():
            dep_node = node_map.get(dependency.node)

            if dep_node is None:
                # Skip dependencies on nodes that are automatically
                # inserted by upper layers (e.g. input nodes)
                continue

            # Reassign dependencies on subpolicies.
            # If a node depends on a subpolicy, it'll instead depend
            # on any of the leaves of that subpolicy.
            if dep_node.id in replacement_dependencies:
                replacement_dep = replacement_dependencies[dep_node.id]
                node.dependencies[dep_name] = replacement_dep
        resolved.append(node)

    return resolved


def _find_input_node(nodes: list[Node]) -> tuple[int, InputNode]:
    for i, node in enumerate(nodes):
        if node.type == NodeType.INPUT:
            return i, node
    raise ValueError("Input node not found in the list of nodes")


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
