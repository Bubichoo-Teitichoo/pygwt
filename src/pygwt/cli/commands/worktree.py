"""Worktree commands."""

import subprocess
import sys
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import click
from click.shell_completion import CompletionItem
from loguru import logger

from pygwt import git
from pygwt.cli.click import decorators
from pygwt.config import Registry
from pygwt.misc import pushd


def shell_complete_branches(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Create a list of branches that match the given incomplete branch name."""
    return [x for x in git.get_branches() if x.startswith(incomplete)]


def shell_complete_branches_add(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Create a list of branches that match the given incomplete branch name."""
    worktree_branches = [x[1] for x in git.worktree_list()]
    return [x for x in git.get_branches() if x.startswith(incomplete) and x not in worktree_branches]


def shell_complete_worktrees(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str | CompletionItem]:
    """Create a list of worktrees for the given incomplete branch name."""
    repository = ctx.params.get("repository", ".")

    with pushd(repository):
        worktrees: dict[str, Path] = {x[1]: x[0] for x in git.worktree_list()}
        if ctx.params.get("create", False):
            return [b for b in shell_complete_branches(ctx, param, incomplete) if b not in worktrees]
        return [CompletionItem(n, help=str(p)) for n, p in worktrees.items() if n.startswith(incomplete)]


def shell_complete_worktrees_remove(
    ctx: click.Context,  # noqa: ARG001
    param: click.Parameter,  # noqa: ARG001
    incomplete: str,
) -> list[CompletionItem]:
    """Create a list of completions items listing worktree directories of the current repository."""
    return [
        CompletionItem(x[0], help=f"{x[1]}@{x[2][:7]}") for x in git.worktree_list() if str(x[0]).startswith(incomplete)
    ]


@click.command()
@click.argument("url", type=str, callback=lambda *args: urlparse(args[2]))
@click.argument(
    "dest",
    type=click.Path(
        exists=False,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
        path_type=Path,
    ),
    default=Path.cwd(),
)
@decorators.common
def clone(url: ParseResult, dest: Path) -> None:
    """Clone a repository and set it up for a `git twig` based workflow.

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
        logger.error(f"Destination already exists: {dest.resolve()}")
        sys.exit(1)

    dest = dest.joinpath(".git")

    with pushd(dest, create=True, parents=True):
        git.execute("init", "--bare")
        git.execute("remote", "add", "origin", url.geturl())
        git.execute("config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
        git.execute("fetch", "--all")
        git.execute("remote", "set-head", "origin", "-a")

    Registry().repositories.append(dest.parent)


@click.command("add")
@click.argument(
    "branch",
    type=str,
    shell_complete=shell_complete_branches_add,
)
@click.argument(
    "start-point",
    type=str,
    default=lambda: None,
    shell_complete=shell_complete_branches,
)
@click.option(
    "--dest",
    type=Path,
    default=lambda: None,
    show_default=False,
    help="""Destination path for the new worktree directory.
              If omitted the the destination is inferred from the repository root + branch name.""",
)
@decorators.common
def add(branch: str, dest: Path | None, start_point: str | None) -> None:
    """Create a new worktree.

    Create a new worktree for the given [BRANCH] at the given [DEST].

    If no local branch with the given name exists,
    a new one will be created.

    If one of the remote branches matches the given branch name,
    the newly created branch will track that remote branch.

    If no remote branch exists,
    the newly created branch will be forked off of [START POINT].
    If [START POINT] is omitted, `HEAD` will be used instead.
    """
    try:
        dest, _ = git.worktree_add(branch, dest=dest, start_point=start_point)
    except subprocess.SubprocessError:
        sys.exit(1)


@click.command("list")
@decorators.common
def ls() -> None:
    """List all worktrees."""
    worktrees = git.worktree_list()
    length = max(len(str(x[0])) for x in worktrees)

    for path, name, sha in worktrees:
        click.echo(f"{str(path).ljust(length)} ({name}@{sha[:7]})")


@click.command()
@click.argument("name", type=str, shell_complete=shell_complete_worktrees)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=shell_complete_branches)
@click.option(
    "-c",
    "--create",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Create new worktree from a local or remote branch.",
)
@decorators.common
def switch(name: str, start_point: str | None, *, create: bool) -> None:
    """Switch to a different worktree.

    > [!NOTE]
    > This requires the Shell hooks included in the init scripts.
    > Otherwise it will just print the worktree path

    Under the hood worktrees are given an abstract name.
    With this command [NAME] is the branch name the worktree represents.

    This command works similar to `git switch` for branches.
    If a worktree does not exist the 'create'-flag can be used
    to create a new one before switching to it.

    The create flag will also create a new branch,
    if no branch for the given name could be found.
    If [START-POINT] is omitted, the current `HEAD` is used.

    If [NAME] is `-` you will switch to the previous worktree.
    """
    config = Registry()
    if name == "-":
        if config.last_worktree is not None:
            click.echo(config.last_worktree)
        else:
            logger.error("No last worktree/branch to switch to...")
            sys.exit(1)
    else:
        dest: Path | None = None
        for path, branch, _ in git.worktree_list():
            if name == branch:
                dest = path
                break
        # If dest is None, there is not worktree that has the given branch checked out...
        if dest is None:
            if not create:
                logger.error(f"No worktree that has '{name}' checked out.")
                logger.info("Use the '-c'/'--create' flag to create the worktree.")
                sys.exit(1)

            dest, _ = git.worktree_add(name, start_point=start_point)

        click.echo(dest)
    config.last_worktree = Path.cwd()


@click.command()
@click.argument("worktrees", nargs=-1, type=str, shell_complete=shell_complete_worktrees_remove)
@click.option(
    "-f",
    "--force",
    is_flag=True,
    default=False,
    show_default=True,
    help="Force removal even if worktree is dirty or locked",
)
def remove(worktrees: list[str], *, force: bool) -> None:
    """Remove a worktree.

    This is just an 'alias' for `git worktree remove`
    that's suppose to save you some typing.
    """
    # Let git handle the clean-up and removal.
    # Less pain for us and a known working state afterwards.
    try:
        for worktree in worktrees:
            git.worktree_remove(worktree, force=force)
    except subprocess.SubprocessError:
        sys.exit(1)


@click.command()
@click.argument("name", type=str, shell_complete=shell_complete_worktrees)
@click.argument(
    "start_point",
    type=str,
    default=lambda: None,
    shell_complete=shell_complete_branches,
)
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

    from pygwt.misc import Shell

    logger.warning("This command may have some unexpected side-effects.")
    logger.warning("It's recommended to use 'git wt switch' instead")

    dest: Path | None = None
    for path, branch, _ in git.worktree_list():
        if name == branch:
            if create:
                logger.error(f"Unable to create worktree for branch '{name}'. Worktree already exist at {path}.")
                sys.exit(1)
            dest = path
            break
    # If dest is None, there is not worktree that has the given branch checked out...
    if dest is None:
        if not create:
            logger.error(f"No worktree that has '{name}' checked out.")
            logger.info("Use the '-c'/'--create' flag to create the desired worktree.")
            sys.exit(1)

        dest, _ = git.worktree_add(name, start_point=start_point)

    # If we're inside a bare checkout,
    # Git will set GIT_DIR when executing an alias.
    # Because of that Git will think that we're on the HEAD branch,
    # if in fact we're within a worktree.
    git_dir_env = os.environ.pop("GIT_DIR", None)
    Shell.detect().spawn(dest)
    if git_dir_env is not None:
        os.environ["GIT_DIR"] = git_dir_env

    if create and delete:
        logger.info(f"Removing temporary worktree: {dest}")
        git.worktree_remove(str(dest))
