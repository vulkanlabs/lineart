import ast

from jinja2 import Template


def validate_user_code(user_code: str):
    """Validate, parse and compile custom user code.

    WARNING: this function is *obviously* sensitive. It should only ever
    be run in isolated environments, and the user code in question
    should never be executed. Doing otherwise allows arbitrary code to
    execute, and may cause crashes even with "well-intentioned" code.
    """

    if not isinstance(user_code, str):
        raise TypeError(f"Expected user code as string, got ({type(user_code)})")

    node_name = "vulkan_user_code"
    udf_code = udf(node_name, user_code)
    try:
        parsed = ast.parse(
            source=udf_code,
            filename=node_name,
            mode="exec",
            type_comments=True,
        )
        _ = compile(
            parsed,
            filename=node_name,
            mode="exec",
        )
    except ValueError as e:
        raise UserCodeException("Invalid symbol (\0) in user code") from e
    except SyntaxError as e:
        raise UserCodeException("User code is invalid") from e

    return f"_udf_{node_name}", udf_code


class UserCodeException(Exception):
    def __init__(self, *args):
        super().__init__(*args)


def udf(name: str, source: str) -> str:
    return _USER_FN_TEMPLATE.render(
        node_name=name,
        source=source,
    )


_USER_FN_STRING = """
def _udf_{{node_name}}(*args, **kwargs):
{{source | indent}}
"""

_USER_FN_TEMPLATE = Template(_USER_FN_STRING)
