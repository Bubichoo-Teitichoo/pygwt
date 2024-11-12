"""
Repository related commands.

The commands in this group can be used to quickly switch between repositories.
"""

from pathlib import Path

import click
import pygit2

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
