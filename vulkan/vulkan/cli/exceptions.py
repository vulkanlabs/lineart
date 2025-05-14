from functools import wraps

import click

from vulkan.cli.context import Context


def log_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            log_error = click.echo
            verbose = False

            if len(args) > 0 and isinstance(args[0], Context):
                ctx = args[0]
                log_error = ctx.logger.error
                verbose = ctx.verbose

            for msg in str(e).split("\n"):
                log_error(msg)

            if verbose:
                raise e

    return wrapper
