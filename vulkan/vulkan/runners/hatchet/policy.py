import logging

from hatchet_sdk import Hatchet, ParentCondition, Workflow
from pydantic import create_model

from vulkan.runners.hatchet.nodes import to_hatchet_nodes
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import Node, NodeType

logger = logging.getLogger(__name__)
DEFAULT_POLICY_NAME = "default_policy"


class HatchetFlow:
    """Converts Vulkan policies to Hatchet workflows."""

    def __init__(self, nodes: list[Node], policy_name: str = DEFAULT_POLICY_NAME):
        self.policy_name = policy_name
        self.nodes = to_hatchet_nodes(nodes)
        self.dependencies = self._extract_dependencies(nodes)
        self._hatchet = Hatchet()

    def _extract_dependencies(
        self, nodes: list[Node]
    ) -> dict[str, dict[str, Dependency]]:
        """Extract dependencies from nodes."""
        return {node.id: node.dependencies or {} for node in nodes if node.dependencies}

    def input_type(self):
        input_node = next((n for n in self.nodes if n.type == NodeType.INPUT), None)
        if input_node is None:
            raise ValueError(f"No input node in policy {self.policy_name}")

        input_schema = input_node.schema
        # Note: dynamic models cannot be pickled under these conditions.
        # Similarly, dynamic user functions can't either!
        # To avoid these issues, we shouldn't try to serialize objects
        # of the HatchetFlow class directly.
        # Instead, we use the fact that Vulkan policies can be recreated
        # from a serializable task specification to ensure this isn't an issue.
        return create_model(
            f"{self.policy_name}_InputModel",
            **input_schema,
        )

    def create_workflow(self) -> Workflow:
        """Create a Hatchet workflow from Vulkan nodes."""
        workflow = self._hatchet.workflow(
            name=self.policy_name,
            input_validator=self.input_type(),
        )

        tasks = {}
        for node in self.nodes:
            parents = []
            skip_conditions = []
            if node.id in self.dependencies:
                for dep in self.dependencies[node.id].values():
                    task = tasks[dep.id]
                    parents.append(task)
                    if dep.output:
                        # Handle conditional dependencies
                        skip_conditions.append(
                            ParentCondition(
                                parent=task,
                                expression=f"output.data != '{dep.output}'",
                            )
                        )

            task_creation_fn = workflow.task(
                name=node.task_name,
                parents=parents,
                skip_if=skip_conditions,
                # execution_timeout=node.execution_timeout,
                # retries=node.retries,
            )
            task = task_creation_fn(node.task_fn())
            tasks[node.id] = task
        return workflow
