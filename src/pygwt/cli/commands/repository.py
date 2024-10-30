"""
Repository related commands.

The commands can be used to quickly switch between repositories.
"""

import logging
import sys
from pathlib import Path

import click
import pygit2

from pygwt import git

_PYGWT_REGISTRY = "wt.registry"
_PYGWT_LAST = "wt.last"
_PATH_TYPE = click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path)


def _read_registry() -> list[str]:
    config = pygit2.Config.get_global_config()
    try:
        registry = config[_PYGWT_REGISTRY]
    except KeyError:
        return []
    return registry.split(",")


def _write_registry(registry: list[str]) -> None:
    config = pygit2.Config.get_global_config()
    config[_PYGWT_REGISTRY] = ",".join(entry.strip() for entry in registry)


def _switch_path(option: str) -> Path:
    if option != "-":
        return _PATH_TYPE(option).resolve()

    config = pygit2.Config.get_global_config()
    return Path(config[_PYGWT_LAST]) if _PYGWT_LAST in config else Path.cwd()


def _shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    registry = _read_registry()
    return [path for path in registry if path.startswith(incomplete)]


@click.command("list")
def list_() -> None:
    """List all registered repositories."""
    for repository in _read_registry():
        click.echo(repository)


@click.command()
@click.argument("path", type=_PATH_TYPE, default=Path.cwd())
def register(path: Path) -> None:
    """Add a repository to the registry of switchable repositories."""
    try:
        repository = git.Repository(path)
    except git.NoRepositoryError:
        logging.error(f"{path} does not contain a git repository")  # noqa: TRY400
        sys.exit(1)

    _write_registry([*_read_registry(), repository.root.as_posix()])


@click.command()
@click.argument("path", type=_switch_path, shell_complete=_shell_complete)
def switch(path: Path) -> None:
    """Switch to a different repository."""
    config = pygit2.Config.get_global_config()
    # store the current path, if we're in a git repository.
    cwd = Path.cwd().as_posix()
    current = cwd if pygit2.discover_repository(cwd) else None

    click.echo(path)
    if current is not None:
        config[_PYGWT_LAST] = current
