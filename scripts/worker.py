import pandas as pd
from hatchet_sdk import Context, EmptyModel, Hatchet
from pydantic import BaseModel

from vulkan.core.policy import Policy
from vulkan.runners.beam.local.runner import PolicyRunner
from vulkan.runners.hatchet.policy import HatchetFlow
from vulkan.schemas import DataSourceSpec
from vulkan.spec.dependency import INPUT_NODE, Dependency
from vulkan.spec.nodes import BranchNode, DataInputNode, TerminateNode
from vulkan.spec.policy import PolicyDefinition


# Branching node
def branch_condition(context, inputs, **kwargs):
    if inputs["score"] > 500:
        return "approved"
    return "denied"


branch = BranchNode(
    func=branch_condition,
    name="branch",
    description="Make a decision based on the data source",
    dependencies={
        "inputs": Dependency(INPUT_NODE),
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
        branch,
        approved,
        denied,
    ],
    input_schema={"tax_id": str, "score": int},
)

p = Policy.from_definition(demo_policy)
flow = HatchetFlow(p.nodes)
hwf = flow.create_workflow()

hatchet = Hatchet()


class SimpleInput(BaseModel):
    message: str


wf = hatchet.workflow(name="SimpleWorkflow")


@wf.task(name="SimpleTask")
def simple(input: SimpleInput, ctx: Context) -> dict[str, str]:
    return {
        "transformed_message": input.message.lower(),
    }


if __name__ == "__main__":
    worker = hatchet.worker(name="test-worker", workflows=[wf, hwf])
    worker.start()
