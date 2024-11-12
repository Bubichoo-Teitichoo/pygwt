import click

from pygwt.cli.commands.repository import _read_registry


@click.command("list")
def list_() -> None:
    """List all registered repositories."""
    for repository in _read_registry():
        click.echo(repository)
