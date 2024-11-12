import logging
import sys
from pathlib import Path

import click

from pygwt import git
from pygwt.cli.commands.repository import _PATH_TYPE, _read_registry, _write_registry


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
