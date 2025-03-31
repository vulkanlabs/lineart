from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import BranchNode, DataInputNode, TerminateNode
from vulkan_public.spec.policy import PolicyDefinition

data_source = DataInputNode(
    name="data_source",
    description="Get external data from a provider",
    source="data-source:api:v0.0.1",
    dependencies={"data": Dependency(INPUT_NODE)},
)


# Branching node
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

approved = TerminateNode(
    name="approved",
    description="Approve customer based on the score",
    return_status="APPROVED",
    dependencies={"condition": Dependency("branch", "approved")},
)

denied = TerminateNode(
    name="denied",
    description="Deny customers that are below minimum",
    return_status="DENIED",
    dependencies={"condition": Dependency("branch", "denied")},
)

demo_policy = PolicyDefinition(
    nodes=[
        data_source,
        branch,
        approved,
        denied,
    ],
    components=[],
    config_variables=["MINIMUM_SCORE"],
    input_schema={"tax_id": str},
)
