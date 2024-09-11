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
import click.shell_completion
import pygit2
from click.shell_completion import CompletionItem

import pygwt.logging
from pygwt import git
from pygwt.completions import PowershellComplete  # noqa: F401 - required to enable powershell completions
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


def all_branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    repository = git.Repository()
    return [branch for branch in repository.branches if branch.startswith(incomplete)]


def branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    repository = git.Repository()
    branches = {}
    for branch in repository.list_remote_branches():
        if branch.branch_name.endswith("HEAD"):
            continue
        name = Path(branch.branch_name).relative_to(branch.remote_name).as_posix()
        branches[name] = CompletionItem(name, help=branch.branch_name)

    for branch in repository.list_local_branches():
        branches[branch.branch_name] = CompletionItem(branch.branch_name)

    return [completion for name, completion in branches.items() if name.startswith(incomplete)]


def worktree_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
    """Create list of worktree names matching the given incomplete name."""
    repository = git.Repository()
    worktrees = [
        CompletionItem(name, help=worktree.path)
        for name, worktree in repository.list_worktrees_ex2().items()
        if name.startswith(incomplete)
    ]
    if ctx.params.get("create", False):
        return branch_shell_complete(ctx, param, incomplete) + worktrees
    return worktrees


def repositories_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
    """Function that creates a list of branches for shell completion."""
    config = pygit2.Config.get_global_config()

    try:
        registry = config["wt.registry"].split(",")
    except KeyError:
        registry = []
    return [path for path in registry if path.startswith(incomplete)]


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


@main.command("clone")
@click.argument("url", type=str, callback=lambda ctx, arg, value: urlparse(value))  # noqa: ARG005
@click.argument(
    "dest",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, resolve_path=True, path_type=Path),
    default=Path.cwd(),
)
@common_decorators
def worktree_clone(url: ParseResult, dest: Path) -> None:
    """Clone a repository and set it up for a `git worktree` based workflow.

    The repository will be cloned as a bare repository,
    which means only the files
    that usually reside in the *.git* subdirectory are created.

    Those files are created in a *.git* directory,
    similar to the regular clone behavior.
    But since the repository is cloned in bare mode
    no other files will be created.
    """
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
@click.argument("start-point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
@click.option(
    "--dest",
    type=str,
    default=lambda: None,
    show_default=False,
    help="""Destination path for the new worktree directory.
              If omitted the the destination is inferred from the repository root + branch name.""",
)
def worktree_add(branch: str, dest: str | None, start_point: str | None) -> None:
    """Add a new worktree.

    Adds a new worktree for the given [BRANCH] at the defined destination.
    If [BRANCH] already exists on the remote,
    the worktree will track the remote branch.

    If [BRANCH] does not exists
    the new branch will be based on the current `HEAD`.
    When [START-POINT] is given
    the newly created branch is based on [START-POINT] instead.
    """
    repository = git.Repository()
    repository.get_worktree(branch, create=True, start_point=start_point, dest=dest)


@main.command("ls")
@common_decorators
def worktree_list() -> None:
    """List all worktrees.

    This is just an alias for for `git worktree list`.
    """
    # git has much more information about the worktree than we can get via libgit
    git_cmd("worktree", "list", check=False, capture=False)


@main.command("switch")
@common_decorators
@click.argument("name", type=str, shell_complete=worktree_shell_complete)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
@click.option(
    "-c",
    "--create",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="Create the worktree if it does not yet exists.",
)
def worktree_switch(name: str, start_point: str, *, create: bool) -> None:
    """Switch to a different worktree.

    > [!NOTE]
    > This requires the Shell hooks included in the completion scripts.
    > Otherwise it will just print the worktree path

    Under the hood worktrees are given an abstract name.
    With this command [NAME] is the branch name the worktree represents.

    This command works similar to `git switch` for branches.
    If a worktree does not exist the 'create'-flag is required to create a new one.

    The create flag will also create a new branch,
    if no branch for the given name could be found.
    If [START-POINT] is omitted,
    the current *HEAD* is used.

    If name is `-` you will switch to the previous directory.
    """
    repository = git.Repository()
    pcwd = Path.cwd().as_posix()
    if name == "-":
        try:
            last = repository.config["wt.last"]
            click.echo(last)
        except KeyError:
            logging.error("No last worktree/branch to switch to...")  # noqa: TRY400
            click.echo(".")
            sys.exit(1)
    else:
        worktree = repository.get_worktree(name, create=create, start_point=start_point)
        repository.config["wt.last"] = Path.cwd().as_posix()
        click.echo(worktree.path)
    repository.config["wt.last"] = pcwd


@main.command(
    "rm",
    context_settings={
        "ignore_unknown_options": True,
    },
)
@click.argument("name", type=str, shell_complete=worktree_shell_complete)
@click.argument("additional_args", nargs=-1, type=click.UNPROCESSED)
def worktree_remove(name: str, additional_args: list[str]) -> None:
    """Remove a worktree.

    This is just an 'alias' for `git worktree remove`
    that's suppose to save you some typing.
    """
    # Let git handle the clean-up and removal.
    # Less pain for us and a known working state afterwards.
    git_cmd("worktree", "remove", name, *additional_args, check=False, capture=False)


@main.command("lsr")
def worktree_list_registry() -> None:
    """List all registred repositories."""
    try:
        config = pygit2.Config.get_global_config()
        for repo in config["wt.registry"].split(","):
            click.echo(repo)
    except KeyError:
        ...


@main.command("register")
@click.argument("path", type=click.Path(exists=True, dir_okay=True, file_okay=False, path_type=Path), default=".")
def worktree_register(path: Path) -> None:
    """Add a repository to the registry of switchable repositories."""
    try:
        repository = git.Repository(path)
    except git.NoRepositoryError:
        logging.error(f"{path} does not contain a repository")  # noqa: TRY400
        sys.exit(1)

    config = pygit2.Config.get_global_config()

    try:
        registry = config["wt.registry"]
        config["wt.registry"] = ",".join([*registry.split(","), repository.root.as_posix()])
    except KeyError:
        config["wt.registry"] = repository.root.as_posix()


@main.command("switchr")
@click.argument(
    "path",
    type=str,
    shell_complete=repositories_shell_complete,
)
def workree_repository_switch(path: str) -> None:
    """Switch to a different repository."""
    config = pygit2.Config.get_global_config()
    # store the current path, if we're in a git repository.
    current = Path.cwd().as_posix() if pygit2.discover_repository(Path.cwd().as_posix()) is not None else None

    if path == "-":
        try:
            path = config["wt.last"]
        except KeyError:
            logging.error("No last worktree to switch to...")  # noqa: TRY400
            click.echo(".")
            sys.exit(1)

    click.echo(path)
    if current is not None:
        config["wt.last"] = current


@main.command("shell")
@common_decorators
@click.argument("name", type=str, shell_complete=worktree_shell_complete)
@click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
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
    """Spawn a new shell within the selected worktree.

    > [!WARNING]
    > This command spawns a new shell,
    > which may result in some unexpected side-effects.
    > Consider using `pygwt switch` instead.

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

    logging.warning("This command may have some unexpected side-effects.")
    logging.warning("It's recommended to use 'pygwt switch' instead")

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
