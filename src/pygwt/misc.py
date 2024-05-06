"""Miscellaneous helper classes and functions."""

from __future__ import annotations

import logging
import os
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from types import TracebackType

    from typing_extensions import Self


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

    def __init__(self, path: str | Path, *, create: bool = False) -> None:
        """
        Create a new Instance.

        Args:
            path (Path):
                The path you'd like to switch to,
                as soon as the context management block is entered.
            create (bool):
                When set to true the destination directory
                and all it's parents that do not yet exists are created.
        """
        self.__origin: Path = Path.cwd()
        self.__dest: Path = Path(path).resolve()
        self.__create: bool = create

    def __enter__(self) -> Self:
        """Change the working directory to the configured path."""
        if self.__create:
            logging.debug(f"Creating if not exists: {self.__dest}")
            self.__dest.mkdir(parents=True, exist_ok=True)
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
