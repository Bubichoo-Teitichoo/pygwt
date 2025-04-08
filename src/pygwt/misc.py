"""Miscellaneous helper classes and functions."""

from __future__ import annotations

import contextlib
import logging
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from collections.abc import Generator


class IterableEnum(Enum):
    """Extension to base Enum that adds convenience function for creation lists from the names and values."""

    @classmethod
    def names(cls: type[IterableEnum]) -> list[str]:
        """
        Get a list of all Enum literals.

        Args:
            cls (type[IterableEnum]):
                The enum class object.

        Returns:
            list[str]:
                The list of Enum literals.
        """
        return [literal.name for literal in cls]

    @classmethod
    def values(cls: type[IterableEnum]) -> list[str]:
        """
        Get a list of all Enum values.

        Args:
            cls (type[IterableEnum]):
                The Enum class object.

        Returns:
            list[str]:
                The list of Enum values.
        """
        return [literal.value for literal in cls]


@contextlib.contextmanager
def pushd(
    path: str | os.PathLike | Path,
    *,
    create: bool = False,
    parents: bool = False,
    exist_ok: bool = False,
) -> Generator[tuple[Path, Path], None, None]:
    """
    A "reinterpretation" of the popular pushd bash command in Python.

    The class is designed to be used with a context management block (`with`).

    Example:
        ```python
        with pushd("foo/bar"):
            # do something within "foo/bar"
            ...
        ```

    Args:
        path (str | os.PathLike | Path):
            The path you'd like to switch to.
        create (bool, optional):
            If set the directory `path` points to will be created.
            Defaults to `False`.
        parents (bool, optional):
            Create all none-existing parent directories.
            Requires `create` to be set.
            Defaults to `False`.
        exist_ok (bool, optional):
            Do not raise an exception if the directory `path` points to already exists.
            Defaults to `False`.
    """
    path = Path(path)
    cwd = Path.cwd()

    if create:
        path.mkdir(parents=parents, exist_ok=exist_ok)

    try:
        logging.debug(f"pushd: {path}")
        os.chdir(path)
        yield (cwd, path)
    finally:
        logging.debug(f"popd: {path}")
        os.chdir(cwd)


def boolean(val: bool | int | str) -> bool:
    """
    Convert all sorts of boolean literals to an actual bool.

    Supported:

    - 1
    - "1"
    - "yes"
    - "on"
    - "true"

    Note:
        If the given value is a string it will be converted to lower case string.

    Args:
        val (int | str):
            The value to convert.

    Returns:
        bool:
            Boolean representing the given value.
    """
    if isinstance(val, str):
        val = val.lower()
    return val in (True, 1, "1", "yes", "on", "true")


class Shell(NamedTuple):
    """Class representation for the results of shellingham."""

    name: str
    """Name of the shell. On Windows the `.exe` suffix is omitted."""
    path: str
    """Path pointing to the executable."""

    @staticmethod
    def detect() -> Shell:
        """
        Tries to detect the shell that executed this program/function.

        This function takes into account that on Windows,
        a Git alias is executed within an instance of sh
        that comes bundled with Git.
        """
        import platform

        import psutil
        import shellingham

        pid: int | None = None
        if platform.system() == "Windows":
            for process in reversed(psutil.Process().parents()):
                if process.name() == "git.exe":
                    pid = process.pid

        return Shell(*shellingham.detect_shell(pid))

    def spawn(self, path: str | Path | None = None) -> None:
        """Spawn a new shell."""
        import subprocess

        path = Path(path) if path else Path.cwd()

        cmd = [self.path]
        match self.name:
            case "cmd" | "powershell" | "pwsh":
                # nothing to do here...
                ...
            case "bash" | "zsh":
                cmd.append("-i")
            case _:
                logging.warning(f"Unsupported Shell: {self.name}. Will try to run it anyway.")
        logging.info(f"Spawning new instance of {self.name} in {path}")
        with pushd(path):
            subprocess.run(cmd, check=False)  # noqa: S603
