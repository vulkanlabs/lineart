from vulkan_dagster.nodes import (
    HTTPConnection,
    Input,
    MultiBranch,
    NodeType,
    Status,
    Transform,
)

input_node = Input(
    name="input_node",
    description="Input node",
    typ=NodeType.INPUT,
    config_schema={"cpf": str},
)

http_params = dict(typ=NodeType.CONNECTION, method="GET", headers={}, params={})

scr_body = Transform(
    func=lambda _, inputs: {"cpf": inputs["cpf"]},
    name="scr_body",
    description="SCR body",
    typ=NodeType.TRANSFORM,
    params={"inputs": "input_node"},
)
scr = HTTPConnection(
    name="scr",
    description="Get SCR score",
    url="http://127.0.0.1:5000/scr",
    dependencies={"body": "scr_body"},
    **http_params,
)


serasa_body = Transform(
    func=lambda _, inputs: {"cpf": inputs["cpf"]},
    name="serasa_body",
    description="Serasa body",
    typ=NodeType.TRANSFORM,
    params={"inputs": "input_node"},
)
serasa = HTTPConnection(
    name="serasa",
    description="Get Serasa score",
    url="http://127.0.0.1:5000/serasa",
    dependencies={"body": "serasa_body"},
    **http_params,
)


# The user function needs to use a set of parameters
# that is defined by previous ops (validated in dagster).
# It also needs to take the context and **kwargs.
def scr_func(context, scr_response, **kwargs):
    context.log.info(f"Received SCR: {scr_response}")
    score = scr_response["score"]
    return score


# Map of parameter names to the ops that define them.
params = {"scr_response": "scr"}
scr_transform = Transform(
    func=scr_func,
    params=params,
    name="scr_transform",
    description="Transform SCR data",
    typ=NodeType.TRANSFORM,
)


def serasa_func(context, serasa_response, **kwargs):
    context.log.info(f"Received Serasa: {serasa_response}")
    score = serasa_response["score"]
    return score


serasa_transform = Transform(
    func=serasa_func,
    name="serasa_transform",
    description="Transform Serasa data",
    typ=NodeType.TRANSFORM,
    params={"serasa_response": "serasa"},
)


def join_func(context, scr_score, serasa_score, **kwargs):
    scores = {"scr_score": scr_score, "serasa_score": serasa_score}
    return scores


join_transform = Transform(
    func=join_func,
    name="join_transform",
    description="Join scores",
    typ=NodeType.TRANSFORM,
    params={"scr_score": "scr_transform", "serasa_score": "serasa_transform"},
)


# Branching node
def branch_condition_1(context, scores, **kwargs):
    if scores["scr_score"] > 600:
        return "approved"
    if scores["serasa_score"] > 800:
        return "analysis"
    return "denied"


branch_1 = MultiBranch(
    func=branch_condition_1,
    name="branch_1",
    description="Branch data",
    typ=NodeType.BRANCH,
    params={"scores": "join_transform"},
    outputs=["approved", "analysis", "denied"],
)


def t_approved(context, inputs, scores, **kwargs):
    context.log.info(f"Approved: {scores}")
    return Status.APPROVED


terminate_1 = Transform(
    func=t_approved,
    name="terminate_1",
    description="Terminate data branch",
    typ=NodeType.TRANSFORM,
    params={"inputs": ("branch_1", "approved"), "scores": "join_transform"},
)


def t_analysis(context, inputs, **kwargs):
    return Status.ANALYSIS


terminate_2 = Transform(
    func=t_analysis,
    name="terminate_2",
    description="Terminate data branch",
    typ=NodeType.TRANSFORM,
    params={"inputs": ("branch_1", "analysis")},
)


def t_denied(context, inputs, **kwargs):
    return Status.DENIED


terminate_3 = Transform(
    func=t_denied,
    name="terminate_3",
    description="Terminate data branch",
    typ=NodeType.TRANSFORM,
    params={"inputs": ("branch_1", "denied")},
)

policy_nodes = [
    input_node,
    scr_body,
    scr,
    serasa_body,
    serasa,
    scr_transform,
    serasa_transform,
    join_transform,
    branch_1,
    terminate_1,
    terminate_2,
    terminate_3,
]
