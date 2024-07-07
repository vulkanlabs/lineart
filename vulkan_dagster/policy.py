from vulkan_dagster.nodes import Branch, HTTPConnection, HTTPConnectionConfig, NodeType, Context, NodeConfig, Transform, Status

context = Context(
    data={
        "cpf": "12345678900"
    },
    variables={}
)

config = HTTPConnectionConfig(
    name="scr",
    description="Get SCR score",
    type=NodeType.CONNECTION,
    url="http://127.0.0.1:5000",
    method="GET",
    headers={},
    params={},
) 
n1 = HTTPConnection(config)

config = NodeConfig(
    name="transform",
    description="Transform data",
    type=NodeType.TRANSFORM,
)

# The user function needs to use a set of parameters
# that is defined by previous ops (validated in dagster).
# It also needs to take the context and **kwargs.
def f2(context, scr_response, **kwargs):
    context.log.info(f"Received SCR: {scr_response}")
    score = scr_response["score"]
    return score * 2

# Map of parameter names to the ops that define them.
p2 = {"scr_response": "scr"}
n2 = Transform(config, f2, p2)


# Branching node
branch_config = NodeConfig(
    name="branch",
    description="Branch data",
    type=NodeType.BRANCH,
)

def branch_condition(context, score, **kwargs):
    return score > 500

p3 = {"score": "transform"}
branch = Branch(
    branch_config, branch_condition, p3, 
    left="left_branch_1",
    right="right_branch_1",)

# process the outputs of our branch op
config_left = NodeConfig(
    name="transform_left",
    description="Transform left data branch",
    type=NodeType.TRANSFORM,
)

def f_left(context, inputs, **kwargs):
    return Status.DENIED

p_left = {"inputs": ("branch", "left_branch_1")}
t_left = Transform(config_left, f_left, p_left)

config_right = NodeConfig(
    name="transform_right",
    description="Transform right data branch",
    type=NodeType.TRANSFORM,
)

def f_right(context, inputs, **kwargs):
    return Status.APPROVED

p_right = {"inputs": ("branch", "right_branch_1")}
t_right = Transform(config_right, f_right, p_right)

policy_nodes = [n1, n2, branch, t_left, t_right]
