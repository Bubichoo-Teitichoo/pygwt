"""Completion util functions."""

from pathlib import Path

import click
from click.shell_completion import CompletionItem

from pygwt import git


def all_branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    repository = git.Repository()
    return [branch for branch in repository.branches if branch.startswith(incomplete)]


def branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:  # noqa: ARG001
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


def worktree_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
    """Create list of worktree names matching the given incomplete name."""
    repository = git.Repository()
    worktrees = [
        CompletionItem(name, help=worktree.path)
        for name, worktree in repository.list_worktrees_ex2().items()
        if name.startswith(incomplete)
    ]
    if ctx.params.get("create", False):
        return branch_shell_complete(ctx, param, incomplete) + worktrees
    return worktrees


def repositories_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    import pygit2

    config = pygit2.Config.get_global_config()

    try:
        registry = config["wt.registry"].split(",")
    except KeyError:
        registry = []
    return [path for path in registry if path.startswith(incomplete)]
