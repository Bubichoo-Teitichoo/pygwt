"""Module that defines differnt kinds of data models that control the applications behavior."""

from pathlib import Path
from typing import ClassVar

from pydantic import BaseModel, Field
from typing_extensions import Self


class Registry(BaseModel):
    """Data model that defines the registry.

    The registry is used for switching back and forth between worktrees
    and repositories,
    and as storage for repositories.
    """

    last_worktree: Path | None = Field(default=None, alias="last-worktree")
    last_repository: Path | None = Field(default=None, alias="last-repository")
    repositories: list[Path] = Field(default_factory=list)

    _instance: ClassVar[Self | None] = None

    def __new__(cls, *args, **kwargs) -> Self:  # noqa: ANN002, ANN003
        """Create a new instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self) -> None:
        """Create a new instance by loading it from a file on disk."""
        import atexit
        import json

        cfg = Path.home().joinpath(".config", "twig", "registry.json")
        cfg.parent.mkdir(parents=True, exist_ok=True)
        if cfg.exists():
            super().__init__(**json.loads(cfg.read_text(encoding="utf-8")))
        else:
            super().__init__()

        atexit.register(lambda: cfg.write_text(self.model_dump_json(indent=4, by_alias=True)))
