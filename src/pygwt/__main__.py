"""Main Module."""

import logging
import shutil
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar
from urllib.parse import ParseResult, urlparse

import click

import pygwt.logging
from pygwt import git
from pygwt.misc import Shell


def git_cmd(cmd: str, *args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
    """
    Execute a git command, with the given arguments.

    Returns:
        subprocess.CompletedProcess[str]:
            The result of the command.
    """
    logging.debug(f"Executing: git {cmd}")
    logging.debug(f"Arguments: {args}")
    return subprocess.run(["git", cmd, *args], check=check, capture_output=capture, text=True, encoding="UTF-8")  # noqa: S603, S607


T = TypeVar("T", bound=Callable)


def common_decorators(func: T) -> T:
    """
    Decorator that adds "global" options and other modifications to the click commands.

    The Decorator applies the following option:

    - help option with `-h` and `--help` to trigger it
        opposed to the `--help` that's added by default.
    - version option

    The Decorator applies the following additional modifiers:

    - Loguru catcher that catches and pretty print exceptions
        and exits afterwards.
    """
    func = click.help_option("-h", "--help")(func)
    func = click.version_option()(func)
    return pygwt.logging.catcher()(func)


def branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    repository = git.Repository()
    remote_branches = []
    for branch in repository.list_remote_branches():
        if branch.branch_name.endswith("HEAD"):
            continue
        remote_branches.append(Path(branch.branch_name).relative_to(branch.remote_name).as_posix())
    branches = sorted(set(list(repository.branches.local) + remote_branches))
    return list(filter(lambda x: x.startswith(incomplete), branches))


@click.group("wt")
@pygwt.logging.option("-l", "--log")
@common_decorators
def main() -> None:
    """A CLI tool to simplify the git worktree workflow."""


@main.group()
@common_decorators
def install() -> None:
    """Installers..."""


@install.command("alias")
@click.argument("name", type=str, default="wt")
@click.option(
    "--scope",
    type=click.Choice(["local", "global", "system", "worktree"], case_sensitive=False),
    default="global",
)
@common_decorators
def install_alias(name: str, scope: str) -> None:
    """Install a Git alias for this application."""
    import pygit2

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
@common_decorators
def install_completions() -> None:
    """Install shell completions for the selected shell."""
    import importlib.resources
    import os
    import shutil

    resource = importlib.resources.files("pygwt.completions")
    with importlib.resources.as_file(resource) as resource_dir:
        completions_dir = Path(os.environ["HOME"]).joinpath(".local", "pygwt", "completions")
        completions_dir.mkdir(parents=True, exist_ok=True)
        shutil.copytree(resource_dir, completions_dir, dirs_exist_ok=True)

    shell = Shell.detect().name
    match shell:
        case "zsh" | "bash":
            logging.info("To enable completions add the following line to your shell config:")
            logging.info(f"source {completions_dir}/{shell}.sh")


@main.command("clone")
@click.argument("url", type=str, callback=lambda ctx, arg, value: urlparse(value))  # noqa: ARG005
@click.argument(
    "dest",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
)
@common_decorators
def worktree_clone(url: ParseResult, dest: Path) -> None:
    """
    Clone a repository and set it up for a git worktree based workflow.

    The repository will be cloned as a bare repository,
    which means only the files
    that usually reside in the *.git* subdirectory are created.

    Those files are created in a *.git* directory,
    similar to the regular clone behavior.
    But since the repository is cloned in bare mode
    no other files will be created.

    After cloning the script will switch into the new directory
    and continues with a few extra configuring steps:

    \b
    1. Create an empty bare repository.
    2. Configure remote.origin.fetch:
        This is important because otherwise we won't get any infos
        about the branch state with respect to the remote.
    3. Fetch all remotes:
        Populates the list of remote branches.
    4. Set `origin/HEAD`, which isn't set by a bare checkout.

    All those steps basically create a "normal" clone,
    with the exception of the missing files.

    \f
    Args:
        url (ParseResult):
            The URL of the repository you'd like to clone.
            If dest is omitted,
            the script will infer the destination for the clone
            from the last part of the given URL.
        dest (Path):
            Path where the repository shall be cloned into.
            This may be a path that only partially exists.
            All missing directories will be created
            during cloning.
    """  # noqa: D301 - escaped blocks are required for proper help format.
    import pygit2

    if dest == Path.cwd():
        dest = dest.joinpath(url.path.split("/")[-1])

    if dest.exists():
        logging.error(f"Destination already exists: {dest.resolve()}")
        return

    dest = dest.joinpath(".git")

    logging.info(f"Cloning '{url.geturl()}' into '{dest}'.")
    pygit2.clone_repository(url.geturl(), dest.as_posix(), bare=True)


@main.command("add")
@common_decorators
@click.argument("branch", type=str, shell_complete=branch_shell_complete)
@click.argument("start-point", type=str, default=lambda: None, shell_complete=branch_shell_complete)
@click.option(
    "--dest",
    type=str,
    default=lambda: None,
    help="""Destination path for the new worktree directory.
              If omitted the the destination is inferred from the current working directory + branch name.""",
)
def worktree_add(branch: str, dest: str | None, start_point: str | None) -> None:
    """
    Add a new worktree.

    Adds a new worktree for the given [BRANCH] at the defined destination.
    If [BRANCH] already exists on the remote,
    the worktree will track the remote branch.

    If [BRANCH] does not exists
    the new branch will be based on `origin/HEAD`.
    When [START-POINT] is given
    the newly created branch is based on [START-POINT] instead.
    """
    repository = git.Repository()
    repository.get_worktree(branch, create=True, start_point=start_point, dest=dest)


@main.command("list")
@common_decorators
def worktree_list() -> None:
    """List all worktrees."""
    repository = git.Repository()
    worktrees = repository.list_worktrees_ex2()

    margin = max(len(x) for x in worktrees) if worktrees else 0

    # include root repository if it's a non bare clone.
    repository = git.Repository(repository.root)
    if not repository.is_bare:
        margin = max([margin, len(repository.head.shorthand)])
        click.echo(f"{repository.head.shorthand.ljust(margin)} {repository.root.as_posix()}")
    for name, worktree in worktrees.items():
        click.echo(f"{name.ljust(margin)} {worktree.path}")


@main.command("shell")
@common_decorators
@click.argument("name", type=str, shell_complete=branch_shell_complete)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=branch_shell_complete)
@click.option(
    "-c",
    "--create",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Create the worktree if it does not yet exists.",
)
@click.option(
    "-d",
    "--delete",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Delete the checkout after exiting the shell.",
)
def worktree_shell(name: str, start_point: str | None, *, create: bool, delete: bool) -> None:
    """
    Spawn a new shell within the selected worktree.

    Detect the current shell,
    the command is executed in
    and spawn a new instance within the directory
    of the worktree defined by [NAME].

    If the branch, defined by [NAME],
    does not exist and the create flag is set,
    a new branch will be created.
    If [START_POINT] is omitted
    the current HEAD will be used as a start point.
    """
    import os

    from pygwt.misc import Shell

    repository = git.Repository()
    try:
        worktree = repository.get_worktree(name, create=create, start_point=start_point)
    except git.NoWorktreeError as exception:
        logging.error(str(exception).strip('"'))  # noqa: TRY400 - I don't want to log the exception.
        logging.info("Use the '-c'/'--create' flag to create a new worktree.")
        sys.exit(1)

    # If we're inside a bare checkout,
    # Git will set GIT_DIR when executing an alias.
    # Because of that Git will think that we're on the HEAD branch,
    # if in fact we're within a worktree.
    git_dir_env = None
    if "GIT_DIR" in os.environ:
        git_dir_env = os.environ.pop("GIT_DIR")
    Shell.detect().spawn(worktree.path)
    if git_dir_env is not None:
        os.environ["GIT_DIR"] = git_dir_env

    if create and delete and not isinstance(worktree, git.FakeWorktree):
        logging.info(f"Removing temporary worktree: {name}")
        shutil.rmtree(worktree.path)
        worktree.prune()


if __name__ == "__main__":
    main()
