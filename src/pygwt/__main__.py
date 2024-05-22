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
from pygwt.misc import Shell, pushd


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
def main() -> int:
    """A CLI tool to simplify the git worktree workflow."""
    try:
        git_cmd("--version", check=True)
    except FileNotFoundError:
        logging.exception("Git does not seem to be installed...exiting.")
        sys.exit(1)

    return 0


@main.group()
@common_decorators
def completions() -> None:
    """Generate Shell completions."""


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

    logging.info(f"Installing Git alias in {scope} scope...")
    logging.info(f"Usage: git {name}")

    git_cmd("config", f"--{scope.lower()}", f"alias.{name}", f"! {GIT_ALIAS_HINT}=1 pygwt $@ #")


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
    if dest == Path.cwd():
        dest = dest.joinpath(url.path.split("/")[-1])

    if dest.exists():
        logging.error(f"Destination already exists: {dest.resolve()}")
        return

    dest = dest.joinpath(".git")

    try:
        with pushd(dest, mode=pushd.Mode.parents):
            git_cmd("init", "--bare", capture=False)
            git_cmd("remote", "add", "origin", url.geturl(), capture=False)
            git_cmd("config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*", capture=False)
            git_cmd("fetch", "--all", capture=False)
            git_cmd("remote", "set-head", "origin", "-a", capture=False)
    except subprocess.CalledProcessError as exception:
        # if any of the actions above fail, remove the destination directory.
        logging.error(f"Unable to create new worktree clone: {exception}")  # noqa: TRY400
        if dest.parent.exists():
            logging.debug(f"Deleting directory: {dest.parent}")
            shutil.rmtree(dest.parent)


@main.command("add")
@common_decorators
@click.argument("branch", type=str, shell_complete=branch_shell_complete)
@click.argument("start-point", type=str, default=lambda: None)
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
    proc = git_cmd("branch", "-a", check=False, capture=True)
    if proc.returncode != 0:
        logging.error("You're not within a Git repository clone!")
        return

    git_cmd("fetch", "--all", capture=False)

    # remove leading white spaces and stars
    # and split at the first white space, to only get the name
    # not some referenced branch.
    branches = {line.strip(" *+").split(" ")[0] for line in proc.stdout.split("\n") if line}

    if start_point is not None and start_point not in branches and f"origin/{start_point}" not in branches:
        logging.error(f"Starting point '{start_point}' does not exists...")
        return

    # set checkout destination...
    # if dest was not given, set it to the branch name
    dest = dest or branch

    # if the branch already exists, we set up a worktree
    # that tracks that branch
    if branch in branches or f"remotes/origin/{branch}" in branches:
        logging.info(f"Creating new worktree for existing Branch: {branch} -> {Path(dest).resolve()}")
        git_cmd("worktree", "add", "-B", branch, dest, f"origin/{branch}", capture=False)
    # if that is not the case, the branch must be new, so we create it locally
    else:
        logging.info(f"Creating new branch and worktree: {branch} -> {dest}")
        git_cmd("worktree", "add", "-b", branch, dest, capture=False)
        # By default worktree will choose the base of the current working directory.
        # If that isn't the one the user wants reset the new branch to that particular branch.
        if start_point is not None:
            with pushd(dest):
                logging.info(f"Resetting new Branch to state of '{start_point}'")
                git_cmd("reset", "--hard", f"{start_point}", capture=False)


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
    "-t",
    "--temporary",
    type=bool,
    is_flag=True,
    default=False,
    show_default=True,
    help="""
    Delete the checkout after exiting the shell.
    (Only applied when `--checkout` is given and the worktree doesn't exists yet)
    """,
)
def worktree_shell(name: str, *, create: bool, temporary: bool) -> None:
    """
    Spawn a new shell within the selected worktree.

    Detect the current shell,
    the command is executed in
    and spawn a new instance within the directory
    of the worktree defined by [NAME].
    """
    import hashlib
    import os

    from pygwt.misc import Shell

    repository = git.Repository()
    try:
        # make sure that the given name does not refer
        # to a non-bare root
        root = git.Repository(repository.root)
        if not root.is_bare and root.head.shorthand == name:
            logging.debug("Given name refers to the repository root.")
            worktree = root.as_worktree()
        else:
            # check if the worktree already exists...
            worktree = repository.lookup_worktree_ex(name)
            if worktree.is_prunable:
                logging.info(f"'{name}' exists but is marked as prunable. Run 'git worktree prune' first.")
                sys.exit(1)
        if temporary:
            logging.debug(f"{name} already exists. Disabling `temporary` option")
            temporary = False
    except KeyError:
        if create:
            path = repository.root.joinpath(name).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)

            branch = repository.get_branch(name, create=True)
            worktree_name = hashlib.sha1(name.encode()).hexdigest()  # noqa: S324 - SHA1 is sufficient...
            logging.info(f"Creating new worktree: {name} -> {path}")
            worktree = repository.add_worktree(worktree_name, path.as_posix(), branch)
        else:
            logging.error(f"{name} is not an existing worktree")  # noqa: TRY400 - I don't want to log the exception.
            sys.exit(1)

    # If we're inside a bare checkout,
    # Git will set GIT_DIR when executing an alias.
    # Because of that Git will think that we're on the HEAD branch,
    # if in fact we're within a worktree.
    git_dir_env = os.environ.get("GIT_DIR", "")
    os.environ["GIT_DIR"] = ""
    Shell.detect().spawn(worktree.path)
    os.environ["GIT_DIR"] = git_dir_env

    if create and temporary and not isinstance(worktree, git.FakeWorktree):
        logging.info(f"Removing temporary worktree: {name}")
        shutil.rmtree(worktree.path)
        worktree.prune()


if __name__ == "__main__":
    main()
