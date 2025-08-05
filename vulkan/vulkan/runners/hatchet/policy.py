import logging
from typing import Any, Dict, List, Optional

import requests
from hatchet_sdk import Context, Hatchet, step, workflow

from vulkan.core.run import RunStatus
from vulkan.runners.hatchet.nodes import HatchetNode, to_hatchet_nodes
from vulkan.runners.hatchet.run_config import RUN_CONFIG_KEY, HatchetRunConfig
from vulkan.spec.dependency import Dependency
from vulkan.spec.nodes import Node

logger = logging.getLogger(__name__)
DEFAULT_POLICY_NAME = "default_policy"


class HatchetFlow:
    """Converts Vulkan policies to Hatchet workflows."""

    def __init__(self, nodes: List[Node], policy_name: str = DEFAULT_POLICY_NAME):
        self.policy_name = policy_name
        self.nodes = to_hatchet_nodes(nodes)
        self.dependencies = self._extract_dependencies(nodes)
        self.workflow_fn = self._create_workflow()

    def _extract_dependencies(
        self, nodes: List[Node]
    ) -> Dict[str, Dict[str, Dependency]]:
        """Extract dependencies from nodes."""
        return {node.id: node.dependencies or {} for node in nodes if node.dependencies}

    def _create_workflow(self):
        """Create the Hatchet workflow function."""

        @workflow(name=self.policy_name)
        class VulkanWorkflow:
            def __init__(self):
                self.nodes_map = {node.task_name: node for node in self.nodes}

            @step()
            def execute_workflow(self, context: Context) -> Dict[str, Any]:
                """Execute the entire workflow."""
                results = {}

                # Execute nodes in dependency order
                execution_order = self._get_execution_order()

                for node_name in execution_order:
                    node = self.nodes_map.get(node_name)
                    if node:
                        try:
                            # Prepare inputs for this node
                            node_inputs = self._prepare_node_inputs(
                                node_name, results, context
                            )

                            # Update context with inputs
                            context.additional_metadata.update(node_inputs)

                            # Execute the node
                            task_fn = node.task_fn()
                            result = task_fn(context)
                            results[node_name] = result

                            logger.info(f"Executed node {node_name} successfully")

                        except Exception as e:
                            logger.error(f"Failed to execute node {node_name}: {e}")
                            self._notify_failure(context, str(e))
                            raise

                return results

            def _get_execution_order(self) -> List[str]:
                """Determine the execution order based on dependencies."""
                # Simple topological sort implementation
                visited = set()
                temp_visited = set()
                order = []

                def visit(node_name: str):
                    if node_name in temp_visited:
                        raise ValueError(
                            f"Circular dependency detected involving {node_name}"
                        )
                    if node_name in visited:
                        return

                    temp_visited.add(node_name)

                    # Visit dependencies first
                    node_deps = self.dependencies.get(node_name, {})
                    for dep_key, dep in node_deps.items():
                        if hasattr(dep, "id"):
                            visit(dep.id)
                        elif hasattr(dep, "node"):
                            visit(dep.node)

                    temp_visited.remove(node_name)
                    visited.add(node_name)
                    order.append(node_name)

                # Visit all nodes
                for node in self.nodes:
                    if node.task_name not in visited:
                        visit(node.task_name)

                return order

            def _prepare_node_inputs(
                self, node_name: str, results: Dict[str, Any], context: Context
            ) -> Dict[str, Any]:
                """Prepare inputs for a node based on its dependencies."""
                node_inputs = {}
                node_deps = self.dependencies.get(node_name, {})

                for input_key, dep in node_deps.items():
                    dep_node_name = dep.id if hasattr(dep, "id") else dep.node
                    if dep_node_name in results:
                        dep_result = results[dep_node_name]

                        # Handle output key selection
                        if hasattr(dep, "output") and dep.output:
                            if (
                                isinstance(dep_result, dict)
                                and dep.output in dep_result
                            ):
                                node_inputs[input_key] = dep_result[dep.output]
                            else:
                                node_inputs[input_key] = dep_result
                        else:
                            node_inputs[input_key] = dep_result

                return node_inputs

            def _notify_failure(self, context: Context, error_message: str):
                """Notify the server of workflow failure."""
                run_config = context.additional_metadata.get(RUN_CONFIG_KEY)
                if not run_config:
                    return

                server_url = run_config.server_url
                run_id = run_config.run_id

                url = f"{server_url}/runs/{run_id}"
                try:
                    response = requests.put(
                        url,
                        json={
                            "result": error_message,
                            "status": RunStatus.FAILURE.value,
                        },
                    )
                    if response.status_code not in {200, 204}:
                        logger.error(
                            f"Failed to notify failure to {url}: {response.status_code}"
                        )
                except Exception as e:
                    logger.error(f"Error notifying failure: {e}")

        return VulkanWorkflow

    def get_workflow_class(self):
        """Get the workflow class for registration."""
        return self.workflow_fn

    def register_with_worker(self, worker):
        """Register this workflow with a Hatchet worker."""
        try:
            workflow_class = self.get_workflow_class()
            worker.register_workflow(workflow_class)
            logger.info(f"Registered workflow {self.policy_name} with worker")
        except Exception as e:
            logger.error(f"Failed to register workflow {self.policy_name}: {e}")
            raise


def create_hatchet_workflow(
    nodes: List[Node], policy_name: str = DEFAULT_POLICY_NAME
) -> HatchetFlow:
    """Create a Hatchet workflow from Vulkan nodes."""
    return HatchetFlow(nodes, policy_name)
