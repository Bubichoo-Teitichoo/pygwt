import logging
import sys
from pathlib import Path

import click

from pygwt import git
from pygwt.cli.commands import _shell_complete_branches


@click.command()
@click.argument("name", type=str, shell_complete=_shell_complete_branches)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=_shell_complete_branches)
@click.option(
    "-c",
    "--create",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Create the worktree if it does not yet exists.",
)
def switch(name: str, start_point: str, *, create: bool) -> None:
    """Switch to a different worktree.

    > [!NOTE]
    > This requires the Shell hooks included in the completion scripts.
    > Otherwise it will just print the worktree path

    Under the hood worktrees are given an abstract name.
    With this command [NAME] is the branch name the worktree represents.

    This command works similar to `git switch` for branches.
    If a worktree does not exist the 'create'-flag is required to create a new one.

    The create flag will also create a new branch,
    if no branch for the given name could be found.
    If [START-POINT] is omitted,
    the current *HEAD* is used.

    If name is `-` you will switch to the previous directory.
    """
    repository = git.Repository()
    pcwd = Path.cwd().as_posix()
    if name == "-":
        try:
            last = repository.config["wt.last"]
            click.echo(last)
        except KeyError:
            logging.error("No last worktree/branch to switch to...")  # noqa: TRY400
            click.echo(".")
            sys.exit(1)
    else:
        worktree = repository.get_worktree(name, create=create, start_point=start_point)
        repository.config["wt.last"] = Path.cwd().as_posix()
        click.echo(worktree.path)
    repository.config["wt.last"] = pcwd
