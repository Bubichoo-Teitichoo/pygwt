"""Click specific function decorators."""

from collections.abc import Callable
from typing import TypeVar

import click

import pygwt.log

T = TypeVar("T", bound=Callable)


def common(func: T) -> T:
    """
    Decorator that adds "global" options and other modifications to the click commands.

    The Decorator applies the following option:

    - help option with `-h` and `--help` to trigger it
        opposed to the `--help` that's added by default.
    - version option

    The Decorator applies the following additional modifiers:

    - Loguru catcher that catches and pretty print exceptions
        and exits afterwards.
    """
    func = click.help_option("-h", "--help")(func)
    func = click.version_option()(func)
    return pygwt.log.catcher()(func)
