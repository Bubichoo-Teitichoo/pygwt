"""Commands for initialzations."""

from enum import Enum

import click

from pygwt.misc import Shell


class SupportedShell(Enum):
    """Enum definint supported shells."""

    PWSH = "pwsh"
    POWERSHELL = "powershell"
    BASH = "bash"
    ZSH = "zsh"


_ShellChoices = click.Choice([x.name.lower() for x in SupportedShell], case_sensitive=False)


@click.command()
@click.argument("shell", type=_ShellChoices, default=lambda: Shell.detect().name)
def init(shell: str) -> None:
    """Initialize your shell for git-twig and completions."""
    import importlib_resources

    resources = importlib_resources.files("pygwt.resources")
    match SupportedShell(shell):
        case SupportedShell.PWSH | SupportedShell.POWERSHELL:
            shell_script = resources.joinpath("powershell.ps1")
        case SupportedShell.BASH:
            shell_script = resources.joinpath("bash.sh")
        case SupportedShell.ZSH:
            shell_script = resources.joinpath("zsh.sh")
    click.echo(shell_script.read_text("utf-8"))
