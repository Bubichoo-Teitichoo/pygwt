"""Main Module."""

import click
from pygwt.log import catcher

import pygwt.log
from pygwt.completions import PowershellComplete  # noqa: F401 - required to enable powershell completions


def main() -> None:
    from pygwt.cli import commands
    from pygwt.cli.loader import CLIBuilder

    option = pygwt.log.option("-l", "--log")

    CLIBuilder().add_common_options(
        click.help_option("-h", "--help"),
        click.version_option(),
    ).add_direct_decorators(
        catcher(),
    ).build(
        commands,
    ).run()


if __name__ == "__main__":
    main()
