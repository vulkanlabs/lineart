from functools import wraps

import click

from vulkan_public.cli.context import Context


def log_exceptions(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            ctx = args[0] if len(args) > 0 and isinstance(args[0], Context) else None
            log_error = ctx.logger.error if ctx else click.echo
            for msg in str(e).split("\n"):
                log_error(msg)
            raise e

    return wrapper
