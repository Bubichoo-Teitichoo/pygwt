"""Installer commands."""

import logging
from pathlib import Path

import click
import pygit2

from pygwt import git
from pygwt.cli.click import decorators
from pygwt.misc import Shell


@click.group()
@decorators.common
def install() -> None:
    """Installers..."""


@install.command("alias")
@click.argument("name", type=str, default="wt")
@click.option(
    "--scope",
    type=click.Choice(["local", "global", "system", "worktree"], case_sensitive=False),
    default="global",
)
@decorators.common
def install_alias(name: str, scope: str) -> None:
    """Install a Git alias for this application."""
    from pygwt.misc import GIT_ALIAS_HINT

    if name != "wt":
        logging.warning("You've changed the alias name. This may break the shell completions.")

    logging.info(f"Installing Git alias in {scope} scope...")
    logging.info(f"Usage: git {name}")

    match scope:
        case "system":
            config = pygit2.Config.get_system_config()
        case "global":
            config = pygit2.Config.get_global_config()
        case "local" | "worktree":
            config = git.Repository().config
        case _:
            msg = f"Undefined config scope: {scope}"
            raise ValueError(msg)

    config[f"alias.{name}"] = f"! {GIT_ALIAS_HINT}=1 pygwt"


@install.command("completions")
@decorators.common
def install_completions() -> None:
    """Install shell completions for the selected shell."""
    import os
    import shutil

    import importlib_resources

    resource = importlib_resources.files("pygwt")
    with importlib_resources.as_file(resource) as resource_dir:
        home = os.environ["HOME"] if "HOME" in os.environ else os.environ["USERPROFILE"]
        dest_dir = Path(home).joinpath(".local", "pygwt", "completions")
        dest_dir.mkdir(parents=True, exist_ok=True)
        source_dir = resource_dir.joinpath("completions")
        shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)

    shell = Shell.detect().name
    match shell:
        case "zsh" | "bash":
            logging.info("To enable completions add the following line to your shell config:")
            logging.info(f"source {dest_dir}/{shell}.sh")
        case "powershell" | "pwsh":
            logging.info("To enable completions add the following line to your $profile:")
            logging.info(f". {dest_dir}\\powershell.ps1")
            logging.info(
                "It's also recommended to add the following command: "
                "Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete",
            )
