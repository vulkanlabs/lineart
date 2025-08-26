"""
Example demonstrating how to use HatchetPolicyRunner for local development.

This shows how to replicate the workflow from the notebook example using Hatchet.
"""

from vulkan.runners.hatchet.local.runner import HatchetPolicyRunner
from vulkan.schemas import DataSourceSpec
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import (
    BranchNode,
    DataInputNode,
    InputNode,
    TerminateNode,
)
from vulkan.spec.policy import PolicyDefinition


def create_demo_policy() -> PolicyDefinition:
    """Create the demo policy from the notebook example."""

    # Input node for the policy
    input_node = InputNode(
        name="input", description="Policy input", schema={"tax_id": str}
    )

    # Data source node - gets external data
    data_source = DataInputNode(
        name="data_source",
        description="Get external data from a provider",
        data_source="data-source:api:v0.0.1",
        dependencies={"data": Dependency(INPUT_NODE)},
    )

    # Branching node - makes decision based on score
    def branch_condition(context, bureau, **kwargs):
        context.log.info(bureau)
        if bureau["score"] > context.env.get("MINIMUM_SCORE"):
            return "approved"
        return "denied"

    branch = BranchNode(
        func=branch_condition,
        name="branch",
        description="Make a decision based on the data source",
        dependencies={
            "bureau": Dependency(data_source.name),
        },
        choices=["approved", "denied"],
    )

    # Approval termination
    approved = TerminateNode(
        name="approved",
        description="Approve customer based on the score",
        return_status="APPROVED",
        dependencies={"condition": Dependency("branch", "approved")},
    )

    # Denial termination
    denied = TerminateNode(
        name="denied",
        description="Deny customers that are below minimum",
        return_status="DENIED",
        dependencies={"condition": Dependency("branch", "denied")},
    )

    return PolicyDefinition(
        nodes=[
            input_node,
            data_source,
            branch,
            approved,
            denied,
        ],
        config_variables=["MINIMUM_SCORE"],
        input_schema={"tax_id": str},
    )


def main():
    """Example usage of HatchetPolicyRunner."""

    # Create the demo policy
    demo_policy = create_demo_policy()

    # Display the policy structure
    print("Created demo policy with nodes:")
    for node in demo_policy.nodes:
        print(f"  - {node.name}: {node.type.value}")

    # This is what you'd need to use the runner with a real Hatchet instance:
    print("\nTo use HatchetPolicyRunner:")
    print("1. Set environment variables:")
    print("   export HATCHET_SERVER_URL=https://your-hatchet-instance.com")
    print("   export HATCHET_CLIENT_TOKEN=your_client_token")
    print(
        "   export HATCHET_NAMESPACE=your_namespace  # optional, defaults to 'default'"
    )

    print("\n2. Create and use the runner:")
    print("   runner = HatchetPolicyRunner.from_env(demo_policy)")
    print(
        "   result = runner.run({'tax_id': '123'}, config_variables={'MINIMUM_SCORE': 500})"
    )
    print("   print(result.data)")

    print("\nNote: This example creates the runner structure but doesn't actually")
    print("execute since it requires a real Hatchet server connection.")


if __name__ == "__main__":
    main()
