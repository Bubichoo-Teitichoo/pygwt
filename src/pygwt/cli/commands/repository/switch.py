from pathlib import Path

import click
import pygit2

from pygwt.cli.commands.repository import _PYGWT_LAST, _shell_complete, _switch_path


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
