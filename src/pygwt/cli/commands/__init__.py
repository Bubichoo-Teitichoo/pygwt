import logging
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import click
import pygit2
from click.shell_completion import CompletionItem

from pygwt import git

_PATH_TYPE = click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path)


# TODO: check if this can be removed...
# def _all_branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
#     """Function that creates a list of branches for shell completion."""
#     repository = git.Repository()
#     return [branch for branch in repository.branches if branch.startswith(incomplete)]


def _shell_complete_branches(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    repository = git.Repository()
    branches = {}
    for branch in repository.list_remote_branches():
        if branch.branch_name.endswith("HEAD"):
            continue
        name = Path(branch.branch_name).relative_to(branch.remote_name).as_posix()
        branches[name] = CompletionItem(name, help=branch.branch_name)

    for branch in repository.list_local_branches():
        branches[branch.branch_name] = CompletionItem(branch.branch_name)

    return [completion for name, completion in branches.items() if name.startswith(incomplete)]


def _shell_complete_worktree(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
    """Create list of worktree names matching the given incomplete name."""
    repository = git.Repository()
    worktrees = [
        CompletionItem(name, help=worktree.path)
        for name, worktree in repository.list_worktrees_ex2().items()
        if name.startswith(incomplete)
    ]
    if ctx.params.get("create", False):
        return _shell_complete_branches(ctx, param, incomplete) + worktrees
    return worktrees


@click.group()
def main() -> None:
    """Entry point..."""


@main.command()
@click.argument("url", type=str, callback=lambda ctx, arg, value: urlparse(value))  # noqa: ARG005
@click.argument("dest", type=_PATH_TYPE, default=Path.cwd())
def clone(url: ParseResult, dest: Path) -> None:
    """Clone a repository for worktree workflow.

    The repository will be cloned as a bare repository,
    which means only the files
    that usually reside in the *.git* subdirectory are created.

    Those files are created in a *.git* directory,
    similar to the regular clone behavior.
    But since the repository is cloned in bare mode
    no other files will be created.
    """
    if dest == Path.cwd():
        dirname = url.path.split("/")[-1]
        if dirname.endswith(".git"):
            dirname = dirname[:-4]
        dest = dest.joinpath(dirname)

    if dest.exists():
        logging.error(f"Destination already exists: {dest.resolve()}")
        return

    dest = dest.joinpath(".git")

    logging.info(f"Cloning '{url.geturl()}' into '{dest}'.")
    pygit2.clone_repository(url.geturl(), dest.as_posix(), bare=True)


@main.command()
@click.argument("branch", type=str, shell_complete=_shell_complete_branches)
@click.argument("start-point", type=str, default=lambda: None, shell_complete=_shell_complete_branches)
@click.option(
    "--dest",
    type=str,
    default=lambda: None,
    show_default=False,
    help="""Destination path for the new worktree directory.
              If omitted the the destination is inferred from the repository root + branch name.""",
)
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
    repository.get_worktree(branch, create=True, start_point=start_point, dest=dest)


@main.command("list")
def list_() -> None:
    """List all worktrees.

    This is just an alias for for `git worktree list`.
    """
    # git has much more information about the worktree than we can get via libgit

    import subprocess

    subprocess.run(["git", "worktree", "list"], check=False)  # noqa: S603, S607


@main.command("rm", context_settings={"ignore_unknown_options": True})
@click.argument("name", type=str, shell_complete=_shell_complete_worktree)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
def remove(name: str, additional_args: list[str]) -> None:
    """Remove a worktree.

    This is just an 'alias' for `git worktree remove`
    that's suppose to save you some typing.
    """
    import subprocess

    # Let git handle the clean-up and removal.
    # Less pain for us and a known working state afterwards.
    subprocess.run(["git", "worktree", "remove", name, *additional_args], check=False)  # noqa: S603, S607
