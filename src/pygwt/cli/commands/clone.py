import logging
from pathlib import Path
from urllib.parse import ParseResult, urlparse

import click
import pygit2

_PATH_TYPE = click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path)


@click.command()
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
