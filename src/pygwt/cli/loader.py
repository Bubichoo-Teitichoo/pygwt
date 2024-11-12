import types
from collections.abc import Callable
from typing import TypeAlias, TypeVar, Generic

import click
from typing_extensions import Self

T = TypeVar("T", click.Command, click.Group)
Decorator: TypeAlias = Callable[[T], T]


class CLIBuilder:
    def __init__(self) -> None:
        self._cli: click.Group | None = None
        self._command_decorators: list[Decorator[click.Command]] = []
        self._direct_decorators = []

    def add_common_options(self, *decorators: Decorator[click.Command]) -> Self:
        self._command_decorators.extend(decorators)
        return self

    def add_direct_decorators(self, *decorators) -> Self:
        self._direct_decorators.extend(decorators)
        return self

    def build(self, pkg: types.ModuleType) -> Self:
        self._cli = self._build(pkg)
        return self

    def run(self) -> None:
        """Execute the CLI."""

        def decorate_commands(cmd: T) -> T:
            # is_group = isinstance(cmd, click.Group)
            for decorator in self._direct_decorators:
                if cmd.callback is not None:
                    cmd.callback = decorator(cmd.callback)
            for decorator in self._command_decorators:
                cmd = decorator(cmd)
            if isinstance(cmd, click.Group):
                for name, subcmd in cmd.commands.items():
                    cmd.commands[name] = decorate_commands(subcmd)
            return cmd

        if self._cli is None:
            msg = "CLI was not initialized properly."
            raise RuntimeError(msg)

        self._cli = decorate_commands(self._cli)
        self._cli()

    def _build(self, pkg: types.ModuleType) -> click.Group:
        import importlib
        import pkgutil

        root = self._load_package_commands(pkg)

        path = pkg.__path__
        prefix = pkg.__name__ + "."
        for _, name, is_pkg in pkgutil.iter_modules(path, prefix):
            module = importlib.import_module(name)

            cmds = [self._build(module)] if is_pkg else self._load_module_commands(module)
            for cmd in cmds:
                root.add_command(cmd)
        return root

    def _load_package_commands(self, module: types.ModuleType) -> click.Group:
        groups, commands = self._extract_disjoint_commands(module)

        match len(groups):
            case 0:
                name = module.__name__.rsplit(".", 1)[1]
                group = click.Group(name=name, commands=commands, help=module.__doc__)
            case 1:
                group = groups[0]
                for cmd in commands:
                    if cmd.name not in group.commands:
                        click.echo(f"Warning: Unbound command in {module.__name__}: { cmd.name }")
            case _:
                msg = f"Multiple command groups defined in the package: {module.__name__}"
                raise RuntimeError(msg)

        return group

    def _load_module_commands(self, module: types.ModuleType) -> list[click.Command]:
        groups, commands = self._extract_disjoint_commands(module)
        for group in groups:
            # filter commands, that are not part of any group and return them individually
            commands = [command for command in commands if command.name not in group.commands]
        return [*groups, *commands]

    def _extract_disjoint_commands(self, module: types.ModuleType) -> tuple[list[click.Group], list[click.Command]]:
        import inspect

        # extract all available commands
        unfiltered = [obj for _, obj in inspect.getmembers(module) if isinstance(obj, click.Command)]
        groups = [obj for obj in unfiltered if isinstance(obj, click.Group)]
        commands = [obj for obj in unfiltered if not isinstance(obj, click.Group)]

        return list(groups), list(commands)
