import logging

import coloredlogs


def init_logger(name: str, level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # By default the install() function installs a handler on the root logger,
    # this means that log messages from your code and log messages from the
    # libraries that you use will all show up on the terminal.
    coloredlogs.install(level=level)

    return logger
