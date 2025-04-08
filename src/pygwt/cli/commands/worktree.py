"""Worktree commands."""

import contextlib
import logging
import subprocess
import sys
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import click

from pygwt import git
from pygwt.cli.click import decorators
from pygwt.cli.completions.functions import all_branch_shell_complete, branch_shell_complete, worktree_shell_complete


@click.command()
@click.argument("url", type=str, callback=lambda ctx, arg, value: urlparse(value))  # noqa: ARG005
@click.argument(
    "dest",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
)
@decorators.common
def clone(url: ParseResult, dest: Path) -> None:
    """Clone a repository and set it up for a `git worktree` based workflow.

    The repository will be cloned as a bare repository,
    which means only the files
    that usually reside in the *.git* subdirectory are created.

    Those files are created in a *.git* directory,
    similar to the regular clone behavior.
    But since the repository is cloned in bare mode
    no other files will be created.
    """
    from pygwt.misc import pushd

    if dest == Path.cwd():
        dirname = url.path.split("/")[-1]
        dirname = dirname.removesuffix(".git")
        dest = dest.joinpath(dirname)

    if dest.exists():
        logging.error(f"Destination already exists: {dest.resolve()}")
        return

    dest = dest.joinpath(".git")

    with pushd(dest, create=True, parents=True):
        git.execute("init", "--bare")
        git.execute("remote", "add", "origin", url.geturl())
        git.execute("config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
        git.execute("fetch", "--all")
        git.execute("remote", "set-head", "origin", "-a")


@click.command("add")
@click.argument("branch", type=str, shell_complete=branch_shell_complete)
@click.argument("start-point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
@click.option(
    "--dest",
    type=str,
    default=lambda: None,
    show_default=False,
    help="""Destination path for the new worktree directory.
              If omitted the the destination is inferred from the repository root + branch name.""",
)
@decorators.common
def add(branch: str, dest: str | None, start_point: str | None) -> None:
    """Add a new worktree.

    Adds a new worktree for the given [BRANCH] at the defined destination.
    If [BRANCH] already exists on the remote,
    the worktree will track the remote branch.

    If [BRANCH] does not exists
    the new branch will be based on the current `HEAD`.
    When [START-POINT] is given
    the newly created branch is based on [START-POINT] instead.
    """
    repository = git.Repository()

    if dest is None:
        if git.Repository(repository.root).is_bare:
            dest = repository.root.joinpath(branch).as_posix()
        else:
            dest = repository.root.joinpath(".worktrees", branch).as_posix()

    branches = [branch.shorthand for branch in repository.list_local_branches()]
    branches.extend(
        [branch.shorthand.removeprefix(f"{branch.remote_name}/") for branch in repository.list_remote_branches()],
    )

    command = ["worktree", "add", dest]
    if branch not in branches:
        command.extend(("-b", branch, start_point or ""))
    else:
        command.append(branch)

    with contextlib.suppress(subprocess.SubprocessError):
        git.execute(*command)


@click.command("list")
@decorators.common
def ls() -> None:
    """List all worktrees.

    This is just an alias for for `git worktree list`.
    """
    # git has much more information about the worktree than we can get via libgit
    git.execute("worktree", "list")


@click.command()
@click.argument("name", type=str, shell_complete=worktree_shell_complete)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
@click.option(
    "-c",
    "--create",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Create the worktree if it does not yet exists.",
)
@decorators.common
def switch(name: str, start_point: str, *, create: bool) -> None:
    """Switch to a different worktree.

    > [!NOTE]
    > This requires the Shell hooks included in the init scripts.
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


@click.command()
@click.argument("names", nargs=-1, type=str, shell_complete=worktree_shell_complete)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Force removal even if worktree is dirty or locked",
)
def remove(names: list[str], *, force: bool) -> None:
    """Remove a worktree.

    This is just an 'alias' for `git worktree remove`
    that's suppose to save you some typing.
    """
    # Let git handle the clean-up and removal.
    # Less pain for us and a known working state afterwards.
    with contextlib.suppress(subprocess.SubprocessError):
        for name in names:
            git.execute("worktree", "remove", name, "--force" if force else "")


@click.command()
@click.argument("name", type=str, shell_complete=worktree_shell_complete)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
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
@decorators.common
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
    import shutil

    from pygwt.misc import Shell

    logging.warning("This command may have some unexpected side-effects.")
    logging.warning("It's recommended to use 'pygwt switch' instead")

    repository = git.Repository()
    try:
        worktree = repository.get_worktree(name, create=create, start_point=start_point)
    except git.NoWorktreeError as exception:
        logging.error(str(exception).strip('"'))  # noqa: TRY400 - I don't want to log the exception.
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
