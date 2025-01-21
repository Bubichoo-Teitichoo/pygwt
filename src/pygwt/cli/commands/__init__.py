import click

import pygwt.logging
from pygwt.cli.click import decorators
from pygwt.cli.commands.init import init, uninit
from pygwt.cli.commands.repository import repository
from pygwt.cli.commands.worktree import add, clone, ls, remove, shell, switch


@click.group("wt")
@pygwt.logging.option("-l", "--log")
@decorators.common
def main() -> None:
    """A CLI tool to simplify the git worktree workflow."""


main.add_command(add)
main.add_command(clone)
main.add_command(remove)
main.add_command(shell)
main.add_command(switch)
main.add_command(ls)
main.add_command(repository)
main.add_command(init)
main.add_command(uninit)
