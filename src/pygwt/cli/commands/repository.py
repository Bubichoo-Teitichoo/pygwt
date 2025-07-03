"""Repository related commands."""

import sys
from pathlib import Path

import click
from loguru import logger

from pygwt import git
from pygwt.cli.commands.worktree import shell_complete_worktrees
from pygwt.config import Registry
from pygwt.misc import pushd

_PATH_TYPE = click.Path(exists=True, dir_okay=True, file_okay=False, resolve_path=True, path_type=Path)


def _repository_callback(ctx: click.Context, param: click.Parameter, value: str | Path) -> Path:  # noqa: ARG001
    if value == "-":
        config = Registry()
        if config.last_repository is None:
            logger.error("No last repository to switch to.")
            sys.exit(1)
        click.echo(config.last_repository)
        sys.exit(0)
    return _PATH_TYPE(value)


def _shell_complete_repositories(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    return list(filter(lambda x: x.startswith(incomplete), map(str, Registry().repositories)))


@click.group()
def repository() -> None:
    """List, switch and register repositories.

    Once registered, git-twig allows you to switch to repositories,
    making the usual `cd ../../other/repository` obsolete.
    """


@repository.command("list")
def ls() -> None:
    """List all registred repositories."""
    for repository in Registry().repositories:
        click.echo(repository)


@repository.command()
@click.argument("path", type=_PATH_TYPE, default=Path.cwd().resolve())
def register(path: Path) -> None:
    """Add a repository to the registry of repositories.

    Once registered you can use `git twig repository switch` to switch
    between registered repositories.

    If [PATH] is not given the current working directory is used.
    """
    config = Registry()

    try:
        with pushd(path):
            gitdir = git.git_dir(common=True)
            logger.info(f"Registering {gitdir.parent}")
            config.repositories.append(gitdir.parent)
    except git.GitExecError:
        logger.error(f"{path} does not point to a git repository clone.")
        sys.exit(1)


@repository.command()
@click.argument(
    "repository",
    callback=_repository_callback,
    shell_complete=_shell_complete_repositories,
)
@click.argument(
    "worktree",
    type=str,
    default=lambda: None,
    shell_complete=shell_complete_worktrees,
)
def switch(repository: Path, worktree: str | None) -> None:
    """Switch to a different repository.

    > [!IMPORTANT]
    > For this to work properly
    > you will need the shell integrations,
    > otherwise this command will just print the directory
    > of the repository to switch to.

    Switch to the given [REPOSITORY].
    The repository has to be registered first,
    using the `git twig repository register` command.
    If [REPOSITORY] is `-`,
    you will be returned to the repository
    you've previously called this command from.

    To switch to a specific branch/worktree
    set the [WORKTREE] argument.
    """
    from contextlib import suppress

    config = Registry()

    dest = next((path for path in config.repositories if path == repository), None)
    if dest is not None and worktree is not None:
        with pushd(dest):
            dest = next((x[0] for x in git.worktree_list() if x[1] == worktree), dest)

    if dest is None:
        logger.error(f"No registered repository found under '{repository}'")
        sys.exit(1)

    click.echo(dest)

    with suppress(git.GitExecError):
        git.git_dir(common=True)
        config.last_repository = Path.cwd()
