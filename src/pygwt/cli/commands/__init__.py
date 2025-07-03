import click

import pygwt.log
from pygwt.cli.click import decorators
from pygwt.cli.commands.init import init
from pygwt.cli.commands.repository import repository
from pygwt.cli.commands.worktree import add, clone, ls, remove, shell, switch


@click.group("twig")
@pygwt.log.option("-l", "--log")
@decorators.common
def main() -> None:
    """'git worktree' as it should be...

    Working with git worktree can be a bit finicky at time.
    git-twig aims to make worktrees a first class citizens, similar to branches.

    Using it's shell integration, git-twig makes switching between worktrees as easy as git twig switch...
    """


main.add_command(add)
main.add_command(clone)
main.add_command(remove)
main.add_command(shell)
main.add_command(switch)
main.add_command(ls)
main.add_command(repository)
main.add_command(init)
