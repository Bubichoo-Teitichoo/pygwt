"""Miscellaneous helper classes and functions."""

from __future__ import annotations

import logging
import os
from enum import Enum, IntEnum
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


GIT_ALIAS_HINT: str = "PYGWT_ALIAS"


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


class pushd:  # noqa: N801 - No! It's pushd, deal with it...
    """
    A "reinterpretation" of the popular pushd bash command in Python.

    The class is designed to be used with a context management block (`with`).

    Example:
        ```python
        with pushd("foo/bar"):
            # do something within "foo/bar"
            ...
        ```
    """

    class Mode(IntEnum):
        """
        Modes for the directory operations.

        - create:
            If set, pushd will create the directory before entering it.
        - parents:
            Creates parent directories if they don't exist. (Implies `create`)
        - exist_ok:
            It's not considered an error, if the directory does already exist. (Implies `create`)
        """

        create = 1
        parents = 3
        exist_ok = 5

    def __init__(self, path: str | Path, *, mode: int = 0) -> None:
        """
        Create a new Instance.

        Args:
            path (Path):
                The path you'd like to switch to,
                as soon as the context management block is entered.
            mode (int):
                Bit-mask defining the behavior,
                when changing directories.
                See enum for detailed description.
        """
        self.__origin: Path = Path.cwd()
        self.__dest: Path = Path(path).resolve()
        self.__mode: int = mode

    def __enter__(self) -> Self:
        """Change the working directory to the configured path."""
        if self.__mode & self.Mode.create:
            logging.debug(f"Creating: {self.__dest} Mode: {self.__mode}")

            parents = (self.__mode & self.Mode.parents) == self.Mode.parents
            exists_ok = (self.__mode & self.Mode.exist_ok) == self.Mode.exist_ok
            self.__dest.mkdir(parents=parents, exist_ok=exists_ok)

        logging.debug(f"pushd: {self.__dest}")
        self.__origin = Path.cwd()
        os.chdir(self.__dest)
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Change the working directory, back to the origin."""
        logging.debug(f"popd: {self.__dest}")
        os.chdir(self.__origin)


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
        For that PYGWT_ALIAS must be set.
        """
        import os
        import platform

        import psutil
        import shellingham

        pid: int | None = None
        if platform.system() == "Windows" and boolean(os.environ.get(GIT_ALIAS_HINT, 0)):
            for process in reversed(psutil.Process().parents()):
                if process.name() == "git.exe":
                    pid = process.pid

        return Shell(*shellingham.detect_shell(pid))

    def spawn(self, path: str | Path | None = None) -> None:
        """Spawn a new shell."""
        import subprocess

        path = path or Path.cwd()
        path = Path(path)

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
