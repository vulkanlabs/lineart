import ast
from typing import Callable

from jinja2 import Template


def get_udf_instance(user_code: str) -> Callable:
    try:
        fn_name, udf_code = _validate_user_code(user_code)
    except UserCodeException as e:
        raise e
    # FIXME: this is BAD and should NEVER see the light of day.
    # It is here for quick validation only.
    exec(udf_code)
    udf_instance = locals()[fn_name]
    return udf_instance


def _validate_user_code(user_code: str):
    """Validate, parse and compile custom user code.

    WARNING: this function is *obviously* sensitive. It should only ever
    be run in isolated environments, and the user code in question
    should never be executed. Doing otherwise allows arbitrary code to
    execute, and may cause crashes even with "well-intentioned" code.
    """

    if not isinstance(user_code, str):
        raise TypeError(f"Expected user code as string, got ({type(user_code)})")

    node_name = "vulkan_user_code"
    valid = False

    try:
        parsed = ast.parse(
            source=user_code,
            filename=node_name,
            mode="exec",
            type_comments=True,
        )

        if is_valid_function(parsed, node_name):
            udf_code = user_code
            fn_name = get_fn_name(parsed)
            valid = True
    except Exception:
        # If the user code is not a function, we wrap it in a function
        # and try to parse it again.
        pass

    if not valid:
        udf_code = udf(node_name, user_code)
        fn_name = f"_udf_{node_name}"
        try:
            parsed = ast.parse(
                source=udf_code,
                filename=fn_name,
                mode="exec",
                type_comments=True,
            )
        except ValueError as e:
            raise UserCodeException("Invalid symbol (\0) in user code") from e
        except Exception as e:
            raise UserCodeException("User code is invalid") from e

    try:
        _ = compile(
            udf_code,
            filename=node_name,
            mode="exec",
        )
    except SyntaxError as e:
        raise UserCodeException("User code is invalid") from e

    return fn_name, udf_code


def is_valid_function(tree: ast.Module, node_name: str) -> bool:
    if len(tree.body) != 1:
        return False

    if not isinstance(tree.body[0], ast.FunctionDef):
        return False

    return True


def get_fn_name(tree: ast.Module) -> str:
    assert len(tree.body) == 1
    assert isinstance(tree.body[0], ast.FunctionDef)
    stmt: ast.FunctionDef = tree.body[0]
    return stmt.name


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
