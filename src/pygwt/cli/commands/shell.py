import logging
import shutil
import sys

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
@click.option(
    "-d",
    "--delete",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Delete the checkout after exiting the shell.",
)
def shell(name: str, start_point: str | None, *, create: bool, delete: bool) -> None:
    """Spawn a new shell within the selected worktree.

    > [!WARNING]
    > This command spawns a new shell,
    > which may result in some unexpected side-effects.
    > Consider using `pygwt switch` instead.

    Detect the current shell,
    the command is executed in
    and spawn a new instance within the directory
    of the worktree defined by [NAME].

    If the branch, defined by [NAME],
    does not exist and the create flag is set,
    a new branch will be created.
    If [START_POINT] is omitted
    the current HEAD will be used as a start point.
    """
    import os

    from pygwt.misc import Shell

    logging.warning("This command may have some unexpected side-effects.")
    logging.warning("It's recommended to use 'pygwt switch' instead")

    repository = git.Repository()
    try:
        worktree = repository.get_worktree(name, create=create, start_point=start_point)
    except git.NoWorktreeError as exception:
        logging.error(str(exception).strip('"'))  # noqa: TRY400
        logging.info("Use the '-c'/'--create' flag to create a new worktree.")
        sys.exit(1)

    # If we're inside a bare checkout,
    # Git will set GIT_DIR when executing an alias.
    # Because of that Git will think that we're on the HEAD branch,
    # if in fact we're within a worktree.
    git_dir_env = None
    if "GIT_DIR" in os.environ:
        git_dir_env = os.environ.pop("GIT_DIR")
    Shell.detect().spawn(worktree.path)
    if git_dir_env is not None:
        os.environ["GIT_DIR"] = git_dir_env

    if create and delete and not isinstance(worktree, git.FakeWorktree):
        logging.info(f"Removing temporary worktree: {name}")
        shutil.rmtree(worktree.path)
        worktree.prune()
