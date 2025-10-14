import logging

from hatchet_sdk import Context as HatchetContext
from hatchet_sdk import Hatchet, ParentCondition, Workflow, or_
from pydantic import create_model

from vulkan.core.run import RunStatus
from vulkan.runners.hatchet.nodes import to_hatchet_nodes
from vulkan.runners.shared.app_client import BaseAppClient, create_app_client
from vulkan.runners.shared.constants import RUN_CONFIG_KEY
from vulkan.runners.shared.run_config import VulkanRunConfig
from vulkan.spec.dependency import Dependency
from vulkan.spec.graph import sort_nodes
from vulkan.spec.nodes import Node, NodeType

logger = logging.getLogger(__name__)
DEFAULT_POLICY_NAME = "default_policy"
_NOTIFY_FAILURE = "notify_failure"


class HatchetFlow:
    """Converts Vulkan policies to Hatchet workflows."""

    def __init__(
        self,
        nodes: list[Node],
        policy_name: str = DEFAULT_POLICY_NAME,
        hatchet: Hatchet = None,
    ):
        self.policy_name = policy_name
        self.dependencies = self._extract_dependencies(nodes)
        sorted_nodes = sort_nodes(nodes, self.dependencies)
        self.nodes = to_hatchet_nodes(sorted_nodes)
        if hatchet is None:
            hatchet = Hatchet()
        self._hatchet = hatchet

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

        workflow.on_failure_task(name=_NOTIFY_FAILURE)(_notify_failure)

        tasks = {}
        for node in self.nodes:
            parents = []
            skip_conditions = []
            if node.id in self.dependencies:
                for dep in self.dependencies[node.id].values():
                    task = tasks[dep.id]
                    parents.append(task)

                    # Skip if parent task was skipped
                    skip_conditions.append(
                        ParentCondition(
                            parent=task,
                            expression="output.skipped",
                        )
                    )
                    if dep.output:
                        # Skip if the condition is not met on the parent.
                        skip_conditions.append(
                            ParentCondition(
                                parent=task,
                                expression=f"output.data != '{dep.output}'",
                            )
                        )

            task_creation_fn = workflow.task(
                name=node.task_name,
                parents=parents,
                skip_if=[or_(*skip_conditions)],
            )
            task = task_creation_fn(node.task_fn())
            tasks[node.id] = task
        return workflow


def _notify_failure(wf: Workflow, context: HatchetContext) -> bool:
    run_cfg = context.additional_metadata.get(RUN_CONFIG_KEY)
    if not run_cfg:
        raise RuntimeError("Required resources not available in context")
    run_config = VulkanRunConfig(**run_cfg)
    client: BaseAppClient = create_app_client(**run_cfg)

    context.log(f"Notifying failure for Hatchet run {run_config.run_id}")
    success = client.update_run_status(
        status=RunStatus.FAILURE.value,
        result="",
    )

    if not success:
        msg = f"Failed to notify failure for Hatchet run {run_config.run_id}"
        context.log(msg)
        return {
            "notified": False,
            "message": msg,
            "run_id": run_config.run_id,
        }

    return {
        "notified": True,
        "run_id": run_config.run_id,
    }
