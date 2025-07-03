"""Abstraction layer for pygit2."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Protocol

from loguru import logger

GitExecError = subprocess.CalledProcessError


class NoRepositoryError(FileNotFoundError):
    """Exceptions raised by GitRepository, when no repository was discoverd."""


class NoBranchError(FileNotFoundError):
    """Exception raised by GitRepository, when one of the high-level function could not find a branch."""


class NoWorktreeError(KeyError):
    """Exception raised if a worktree does not exists."""


class Stringifyable(Protocol):
    """A protocol that requires the `__str__` function to be implemented from a specific type."""

    def __str__(self) -> str: ...  # noqa: D105


def execute(cmd: str, *args: Stringifyable | None, capture: bool = False) -> str:
    """Execute a git command."""
    import shutil
    import sys

    path = shutil.which("git")
    if path is None:
        msg = "No 'git' executable found in PATH."
        logger.error(msg)
        raise RuntimeError(msg)

    stdout = sys.stderr if not capture else None

    a = tuple(map(str, filter(bool, args)))
    stdout = subprocess.run([path, cmd, *a], check=True, capture_output=capture, stdout=stdout, text=True).stdout or ""  # noqa: S603
    return stdout.strip()


def get_local_branches() -> list[str]:
    """
    Get a list of locally checked out branches.

    Returns:
        list[str]:
            A list of locally checked out branches.
    """
    return execute("for-each-ref", "--format=%(refname:short)", "refs/heads", capture=True).splitlines()


def get_remote_branches(remote: str = "") -> list[str]:
    """
    Get a list of remote branches.

    Args:
        remote (str, optional):
            The remote, to list the branches for.
            If omitted the branches of all configured remotes are listed.
            Defaults to ''.

    Returns:
        list[str]:
            A list of branches on the selected remote.
    """
    branches = execute("for-each-ref", "--format=%(refname:short)", f"refs/remotes/{remote}", capture=True).splitlines()
    return [x for x in branches if "/" in x]


def get_branches() -> list[str]:
    """Get a list of all branches, local and remote ones."""
    from itertools import chain

    return list(chain(get_remote_branches(), get_local_branches()))


def get_tracking_branch(name: str) -> str | None:
    """Get the remote tracking branch of the given local branch."""
    import contextlib

    with contextlib.suppress(GitExecError):
        return execute("rev-parse", "--abbrev-ref", f"{name}@{{upstream}}", capture=True)
    return None


def git_dir(*, common: bool = False) -> Path:
    """
    Get the '.git' directory of the current worktree.

    Args:
        common (bool, optional):
            If set, the returned path points to the common '.git' directory of the clone.
            Otherwise the path points to the '.git' directory of the current worktree.
    """
    flag = "--git-common-dir" if common else "--git-dir"
    return Path(execute("rev-parse", flag, capture=True)).resolve()


def is_bare() -> bool:
    """
    Check if the worktree is part of a bare repository.

    Returns:
        bool:
            - True: If the current clone is a bare checkout.
            - False: If the current clone is not a bare checkout.
    """
    from pygwt.misc import boolean

    return boolean(execute("rev-parse", "--is-bare-repository", capture=True))


def create_branch(name: str, start_point: str | None) -> str:
    """Helper function to create a branch.

    If the given branch does already exist locally,
    the function will log a warning an return immediately.

    If the given name matches a remote branch (with or without remote prefix),
    a new local branch will be created that is set up to track the remot one.

    If none of the above statements are true,
    the function will create a new local branch with the given name.
    If `start_point` is given,
    the newly created local branch will be forked off of the given branch,
    without tracking it.
    If `start_point` is not given 'HEAD' will be used,
    which points to the currently checked out branch or commit.

    Args:
        name (str):
            Name of the branch that shall be created.
        start_point (str, optional):
            The start point for a new local branch,
            that does not have a matching remote branch.
            Thus this argument is only relevant if a new branch,
            with no remote counterpart exists.
    """
    from functools import partial

    if name in get_local_branches():
        logger.info(f"Unable to create branch. '{name}' already exists.")
        return name

    for remote, branch in map(partial(str.split, sep="/", maxsplit=1), get_remote_branches()):
        if name in (branch, f"{remote}/{branch}"):
            logger.info("Found remote branch...")
            execute("branch", branch, f"{remote}/{branch}")
            return branch

    execute("branch", name, start_point or "HEAD", "--no-track")
    return name


def worktree_add(branch: str, *, dest: Path | None = None, start_point: str | None = None) -> tuple[Path, Path]:
    """Add a new worktree.

    This function will create a new worktree at the given destination.
    If a local branch with the given name exists,
    the branch is checked out into the newly worktree.
    If a remote branch with a matching name exists,
    a new local branch will be created and checked out into the new worktree.

    Args:
        branch (str):
            The name of the branch to create the worktree for.
        dest (Path, optional):
            The destination of the worktree.
            If omitted the destination is either `.worktrees/<branch name>`
            if the clone is a regular one,
            `<git root>/<branch name>` if the clone is a bare clone.
        start_point (str, optional):
            The start point for a new branch.

    Returns:
        tuple[Path, Path]:
            A tuple of Paths where the first one points to the destination
            of the newly created worktree,
            the second one points to the root of the repository clone.

    """
    from pygwt.misc import pushd

    branch = create_branch(branch, start_point)

    with pushd(git_dir(common=True)) as (_, cwd):
        if dest is None:
            subdir = (branch,) if is_bare() else (".worktrees", branch)
            dest = cwd.parent.joinpath(*subdir)

    execute("worktree", "add", dest, branch)
    return dest, cwd.parent


def worktree_remove(worktree: str | Path, *, force: bool = False) -> None:
    """Remove the given worktree.

    Args:
        worktree (str):
            The worktree to remove.
            This shall either be the branch/worktree name,
            or the path of the worktree.
        force (bool):
            Remove the worktree even if it contains uncommited changes.
    """
    execute("worktree", "remove", worktree, "--force" if force else "")


def worktree_list() -> list[tuple[Path, str, str]]:
    """
    List the worktrees of the current clone.

    Returns:
        list[tuple[Path, str, str]]:
            A tuple containing the following informations about the available worktrees:
                - Path: The path the worktree is located at.
                - str: The branch name that is checked out in the worktree
                - str: The commit hash currently checked out in the worktree
    """
    import re

    worktrees = []
    output = execute("worktree", "list", "--porcelain", capture=True)
    for entry in output.split("\n\n"):
        path = re.search(r"^worktree (\S+)$", entry, flags=re.MULTILINE)
        commit = re.search(r"^HEAD (\S+)$", entry, flags=re.MULTILINE)
        branch = re.search(r"^branch refs/heads/(\S+)$", entry, flags=re.MULTILINE)
        if path and commit and branch:
            worktrees.append(
                (
                    Path(path.group(1)),
                    branch.group(1),
                    commit.group(1),
                ),
            )
    return worktrees
