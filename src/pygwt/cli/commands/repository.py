"""Repository related commands."""

import logging
import sys
from pathlib import Path

import click
import pygit2

from pygwt import git
from pygwt.cli.completions.functions import repositories_shell_complete


@click.group()
def repository() -> None:
    """Repository related commands."""


@repository.command("list")
def ls() -> None:
    """List all registred repositories."""
    try:
        config = pygit2.Config.get_global_config()
        for repo in config["wt.registry"].split(","):
            click.echo(repo)
    except KeyError:
        ...


@repository.command()
@click.argument("path", type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path), default=".")
def register(path: Path) -> None:
    """Add a repository to the registry of switchable repositories."""
    try:
        repository = git.Repository(path)
    except git.NoRepositoryError:
        logging.error(f"{path} does not contain a repository")  # noqa: TRY400
        sys.exit(1)

    config = pygit2.Config.get_global_config()

    try:
        registry = config["wt.registry"]
        config["wt.registry"] = ",".join([*registry.split(","), repository.root.as_posix()])
    except KeyError:
        config["wt.registry"] = repository.root.as_posix()


@repository.command()
@click.argument(
    "path",
    type=str,
    shell_complete=repositories_shell_complete,
)
def switch(path: str) -> None:
    """Switch to a different repository."""
    config = pygit2.Config.get_global_config()
    # store the current path, if we're in a git repository.
    current = Path.cwd().as_posix() if pygit2.discover_repository(Path.cwd().as_posix()) is not None else None

    if path == "-":
        try:
            path = config["wt.last"]
        except KeyError:
            logging.error("No last worktree to switch to...")  # noqa: TRY400
            click.echo(".")
            sys.exit(1)

    click.echo(path)
    if current is not None:
        config["wt.last"] = current
