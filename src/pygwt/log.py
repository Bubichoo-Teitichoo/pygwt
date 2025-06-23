"""Bootstrapping for logging and loguru."""

from __future__ import annotations

import sys
from enum import Enum
from typing import TYPE_CHECKING

from loguru import logger

if TYPE_CHECKING:
    from loguru import Catcher


class LogLevel(Enum):
    """Available log levels."""

    trace = "trace"
    debug = "debug"
    info = "info"
    success = "success"
    warning = "warning"
    error = "error"
    critical = "critical"


# mapping of log level to color
COLOR_MAPPING = {
    LogLevel.trace: "<cyan>",
    LogLevel.debug: "<fg #ff00ef>",
    LogLevel.info: "<green>",
    LogLevel.success: "<green>",
    LogLevel.warning: "<yellow>",
    LogLevel.error: "<red>",
    LogLevel.critical: "<red>",
}


# Due to the lazy argument parsing of click,
# the decorator can only be available on the root level.
# If it's added to each command,
# callback would be called each time the default value is applied.
#
# There might be a work around with a customized Option/Parser
# but this will take some serious deep dives into click.
def option(param_name: str, *additional_names: str, default: LogLevel = LogLevel.info):  # noqa: ANN201 - cannot annotate type, because it's unclear what is returned by click
    """Get a pre-configured click option that, that can easily be attached to every function."""
    import click

    def callback(ctx: click.Context, param: click.Parameter, value: str) -> str:  # noqa: ARG001 - protocol requires both arguments
        configure(LogLevel(value))
        return value

    return click.option(
        param_name,
        *additional_names,
        default=default.value,
        type=click.Choice([x.value for x in LogLevel], case_sensitive=False),
        expose_value=False,
        callback=callback,
        is_eager=True,
        help="The minimum log severity level.",
    )


def catcher() -> Catcher:
    """
    Get a pre-configured exception catcher.

    Use this as a decorator for your functions.

    The Catcher will print a stack trace if an exception was caught
    and then exits with exit code 1.

    Returns:
        Catcher:
            A pre-configure Catcher,
            that calls the `sys.exit` function
            when an exception is caught.
    """
    return logger.catch(onerror=lambda *_: sys.exit(1))


def configure(level: LogLevel) -> None:
    """
    Configure loguru's stderr logger with some nice looking defaults.

    Before configuring the logger all loggers are removed.
    Then a new logger that writes to stdout is created,
    with a minimum severity of the given level.

    Args:
        level (LogLevel):
            The minimum severity level for the messages.
    """
    for severity, color in COLOR_MAPPING.items():
        logger.level(severity.value.upper(), color=color)

    logger.remove()
    logger.add(
        sys.stderr,
        level=level.value.upper(),
        format="<level>{level}</level> | {message}",
        colorize=True,
    )
