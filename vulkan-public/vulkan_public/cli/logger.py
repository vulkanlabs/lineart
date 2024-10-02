import logging

import coloredlogs


def init_logger(name: str) -> logging.Logger:
    # Create a logger object.
    logger = logging.getLogger(name)

    # By default the install() function installs a handler on the root logger,
    # this means that log messages from your code and log messages from the
    # libraries that you use will all show up on the terminal.
    coloredlogs.install(level="DEBUG")

    return logger
