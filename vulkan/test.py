
from vulkan.main import (
    Context, NodeType, NodeConfig, Transform, HTTPConnection,
    HTTPConnectionConfig, Policy, Status
)


def test_connection():
    config = HTTPConnectionConfig(
        name="scr",
        description="Get SCR score",
        type=NodeType.CONNECTION,
        url="http://127.0.0.1:5000",
        method="GET",
        headers={},
        params={},
    )
    node = HTTPConnection(config)
    response = node.run({})
    print(response)


# def test_function():
#     config = NodeConfig(
#         name="transform",
#         description="Transform data",
#         type=NodeType.TRANSFORM,
#     )
#     node = Transform(config)
#     response = node.run(lambda x: x, {"x": 1})
#     print(response)


def test_run_policy():
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
    
    def f2(data):
        return data["x"]

    p2 = {"scr": "x"}
    n2 = Transform(config, f2, p2)
    
    def f3(data):
        if data["scr"] > 700:
            return Flow(...)
        return Flow(...)

    n3 = BranchNode(data["scr"] > 700, TerminateNode(Status.APPROVED), Policy())

    policy = Policy(context=context)
    policy.run(nodes=[n1, n2])



# io1
serasa = IO("serasa", ...)

# b1
if serasa["score"] >= 600:
    # r1
    return "approved"

# io2
scr = IO("scr", ...)

# n1
scr_data = parse_scr_data(scr)
scr_score = scr_model.predict(scr_data)

# b2
if scr_score >= 800:
    # r2
    return "denied"


# b3
if scr_score >= 400:
    # io3
    boa_vista = IO("boa_vista", ...)
    # b4
    if boa_vista["score"] >= 700:
        # r3
        return "approved"
    # r4
    return "analysis"

# r5
return "denied"


io1
b1
    r1
    __
    io2
    n1
    b2
        r2
        __
        b3
            r5
            __
            io3
            b4
                r3
                __
                r4