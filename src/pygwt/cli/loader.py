import types

import click


class CLIBuilder:
    def __init__(self) -> None: ...

    def build(self, pkg: types.ModuleType) -> click.Group:
        entry = click.Group(help=pkg.__doc__)
        for group in self._load_pkgs(pkg):
            entry.add_command(group)
        return entry

    def _load_pkgs(self, pkg: types.ModuleType) -> list[click.Command]:
        import importlib
        import pkgutil

        groups: list[click.Command] = self._load_module(pkg)

        path = pkg.__path__
        prefix = pkg.__name__ + "."
        for _, name, is_pkg in pkgutil.iter_modules(path, prefix):
            module = importlib.import_module(name)
            group = click.Group(name[len(prefix) :], help=module.__doc__)
            commands = self._load_pkgs(module) if is_pkg else self._load_module(module)
            for command in commands:
                group.add_command(command)
            groups.append(group)
        return groups

    def _load_module(self, module: types.ModuleType) -> list[click.Command]:
        import inspect

        return [obj for _, obj in inspect.getmembers(module) if isinstance(obj, click.Command)]
