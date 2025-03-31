from enum import Enum
from functools import partial

import requests

from vulkan_public.spec.component import ComponentInstance, ComponentInstanceConfig
from vulkan_public.spec.dependency import INPUT_NODE, Dependency
from vulkan_public.spec.nodes.base import BranchNode, TerminateNode, TransformNode
from vulkan_public.spec.policy import PolicyDefinition

DATA_SERVER_URL = "http://testdata:5000"
CLIENT_SERVER_URL = "http://echo:80/post"

http_params = dict(method="GET", headers={}, params={})


class Status(Enum):
    APPROVED = "APPROVED"
    ANALYSIS = "ANALYSIS"
    DENIED = "DENIED"
    DENIED_SCR_LOW = "DENIED_SCR_LOW"
    APPROVED_SCR = "APPROVED_SCR"


scr_component = ComponentInstance(
    name="scr_component",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="scr_query",
        description="Get SCR score",
        dependencies={"cpf": Dependency(INPUT_NODE, key="cpf")},
        instance_params={"server_url": f"{DATA_SERVER_URL}/scr"},
    ),
)


def _early_return_scr(context, scr_score, **kwargs):
    if scr_score < context.env["CORTE_SCR_RECUSA_AUTOMATICA"]:
        return Status.DENIED_SCR_LOW.value
    if scr_score > context.env["CORTE_SCR_APROVACAO_AUTOMATICA"]:
        return Status.APPROVED_SCR.value

    return "CONTINUE"


early_return_scr = BranchNode(
    name="early_return_scr",
    func=_early_return_scr,
    choices=["CONTINUE", Status.DENIED_SCR_LOW.value, Status.APPROVED_SCR.value],
    dependencies={"scr_score": Dependency(scr_component.config.name)},
)

denied_scr_low = TerminateNode(
    name="denied_scr_low",
    description="TerminateNode data branch",
    return_status=Status.DENIED_SCR_LOW,
    dependencies={
        "condition": Dependency(early_return_scr.name, Status.DENIED_SCR_LOW.value)
    },
)

approved_scr = TerminateNode(
    name="approved_scr",
    description="TerminateNode data branch",
    return_status=Status.APPROVED_SCR,
    dependencies={
        "condition": Dependency(early_return_scr.name, Status.APPROVED_SCR.value)
    },
)


serasa_component = ComponentInstance(
    name="serasa_component",
    version="v0.0.1",
    config=ComponentInstanceConfig(
        name="serasa_sample_query",
        description="Get Serasa score",
        dependencies={
            "cpf": Dependency(INPUT_NODE, key="cpf"),
            "condition": Dependency(early_return_scr.name, "CONTINUE"),
        },
        instance_params={"server_url": f"{DATA_SERVER_URL}/serasa"},
    ),
)


def join_func(context, scr_score, serasa_score, **kwargs):
    scores = {"scr_score": scr_score, "serasa_score": serasa_score}
    return scores


join_transform = TransformNode(
    func=join_func,
    name="join_transform",
    description="Join scores",
    dependencies={
        "scr_score": Dependency(scr_component.config.name),
        "serasa_score": Dependency(serasa_component.config.name),
    },
)


# Branching node
def branch_condition(context, scores, **kwargs):
    context.log.info(f"Policy config: {context.env}")
    if scores["scr_score"] > context.env["CORTE_SCR"]:
        return "approved"
    if scores["serasa_score"] > context.env["CORTE_SERASA"]:
        return "analysis"
    return "denied"


branch_1 = BranchNode(
    func=branch_condition,
    name="branch",
    description="BranchNode data",
    dependencies={"scores": Dependency("join_transform")},
    choices=["approved", "analysis", "denied"],
)

approved = TerminateNode(
    name="approved",
    description="TerminateNode data branch",
    return_status=Status.APPROVED,
    dependencies={"condition": Dependency(branch_1.name, "approved")},
)


analysis = TerminateNode(
    name="analysis",
    description="TerminateNode data branch",
    return_status=Status.ANALYSIS,
    dependencies={"condition": Dependency(branch_1.name, "analysis")},
)

denied = TerminateNode(
    name="denied",
    description="TerminateNode data branch",
    return_status=Status.DENIED,
    dependencies={"condition": Dependency(branch_1.name, "denied")},
)


# TODO: we may want to specify some data to be used in the output.
# Example: return the tax id, status, duration, limit etc
# User-configurable callback
def return_fn(
    context,
    url: str,
    run_id: int,
    return_status: str,
    **kwargs,
) -> bool:
    dagster_run_id: str = context.run_id
    result = requests.post(
        url,
        data={
            "dagster_run_id": dagster_run_id,
            "run_id": run_id,
            "status": return_status,
        },
    )
    if result.status_code not in {200, 204}:
        msg = f"Error {result.status_code} Failed to return status {return_status} to {url} for run {dagster_run_id}"
        context.log.error(msg)
        return False
    return True


demo_policy = PolicyDefinition(
    nodes=[
        early_return_scr,
        denied_scr_low,
        approved_scr,
        join_transform,
        branch_1,
        approved,
        analysis,
        denied,
    ],
    components=[scr_component, serasa_component],
    input_schema={"cpf": str},
    config_variables=[
        "CORTE_SERASA",
        "CORTE_SCR",
        "CORTE_SCR_RECUSA_AUTOMATICA",
        "CORTE_SCR_APROVACAO_AUTOMATICA",
    ],
    # TODO: avisar quando setar uma variavel inutil
    # TODO: permitir setar valor default via spec
    output_callback=partial(return_fn, url=CLIENT_SERVER_URL),
)
