"""Commands for initialzations."""

import shutil
from enum import Enum
from pathlib import Path

import click

from pygwt.misc import Shell


class SupportedShell(Enum):
    """Enum definint supported shells."""

    PWSH = "pwsh"
    POWERSHELL = "powershell"
    BASH = "bash"
    ZSH = "zsh"


@click.command()
@click.argument(
    "shell",
    type=click.Choice([x.name.lower() for x in SupportedShell], case_sensitive=False),
    default=lambda: Shell.detect().name,
)
def init(shell: str) -> None:
    """Initialize your shell for pygwt and completions."""
    import importlib_resources

    path = shutil.which("pygwt")
    if path is None:
        msg = "Unable to detect pygwt installation path."
        raise RuntimeError(msg)
    source = Path(path)
    dest = source.parent.joinpath("git-wt")
    if dest.exists():
        dest.unlink()
    dest.hardlink_to(path)

    resources = importlib_resources.files("pygwt.resources")
    match SupportedShell(shell):
        case SupportedShell.PWSH | SupportedShell.POWERSHELL:
            shell_script = resources.joinpath("powershell.ps1")
        case SupportedShell.BASH:
            shell_script = resources.joinpath("bash.sh")
        case SupportedShell.ZSH:
            shell_script = resources.joinpath("zsh.sh")
    click.echo(shell_script.read_text("utf-8"))


@click.command()
@click.argument(
    "shell",
    type=click.Choice([x.name.lower() for x in SupportedShell], case_sensitive=False),
    default=lambda: Shell.detect().name,
)
def uninit(shell: str) -> None:
    """Reverse the initialize script."""
    path = shutil.which("pygwt")
    if path is None:
        msg = "Unable to detect pygwt installation path."
        raise RuntimeError(msg)
    Path(path).parent.joinpath("git-wt").unlink(missing_ok=True)

    match SupportedShell(shell):
        case SupportedShell.ZSH | SupportedShell.BASH:
            click.echo("_pygwt_uninit")
        case _:
            raise NotImplementedError(shell)
