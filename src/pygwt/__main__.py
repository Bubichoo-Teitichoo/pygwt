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
import pygit2 as git

import pygwt.logging
from pygwt.misc import pushd


class NoRepositoryError(FileNotFoundError):
    """Exceptions raised by GitRepository, when no repository was discoverd."""


class NoBranchError(FileNotFoundError):
    """Exception raised by GitRepository, when one of the high-level function could not find a branch."""


class GitRepository(git.Repository):
    """High-level abstraction for pygit's Repository class."""

    def __init__(self, path: str | None = None) -> None:
        """Create new instance.

        This will use the `discover_repository` method
        and initialize the underlying super class with that.

        Args:
            path (str | None, optional):
                Path of a repository.
                If omitted, the current working directory will be used.
                Defaults to None.

        Raises:
            NoRepositoryError:
                If no repository could be discovered in the given path.
        """
        if path is None:
            path = git.discover_repository(Path.cwd().as_posix())

        if path is None:
            msg = "No repository detected..."
            raise NoRepositoryError(msg)
        super().__init__(path)

    @property
    def root(self) -> Path:
        """
        The root directory of the repository clone.

        Even if the current working directory is within a worktree
        this function will always return the root of the clone
        i.e. the directory containing the `.git` directory.

        Returns:
            Path:
                Path object pointing to the root of the repository clone.
        """
        # this gives us the directory within the .git dir
        # for worktrees this points to a directory under
        # '.git/worktrees/...'
        path = Path(self.path)
        while path.name != ".git":
            path = path.parent
        return path.parent

    def get_branch(self, name: str, *, create: bool = False) -> git.Branch:
        """Abstraction function that's suppose to emulate the behavior or `git switch`.

        This function will first look for a local branch with the given name
        and return it if if exists.

        If not it will look for a remote branch (origin only) with the given name.
        When successful a new local branch with the same name will be create,
        setup to track the remote one and returned.

        If None of the above are options where successful
        and create is set to true a new local branch will be created.
        The newly created branch will be based on the current local HEAD.

        Args:
            name (str):
                Name of the desired branch.
            create (bool, optional):
                If set to `True` and no local branch with the given name exists,
                a new branch will be created.
                Defaults to False.

        Raises:
            NoBranchError:
                If neither local nor remote where found
                and create wasn't set either.


        Returns:
            git.Branch:
                The existing or newly created local branch.
        """
        logging.debug(f"Lookup local branch: {name}")
        # look for already existing local branch
        branch = self.lookup_branch(name, git.enums.BranchType.LOCAL)
        if branch is not None:
            logging.debug(f"Found local branch: {name}")
            return branch

        # look for a remote branch. If one is found create a local tracking branch.
        logging.debug("No local branch found. Looking for remote branch.")
        remote = self.lookup_branch(f"origin/{name}", git.enums.BranchType.REMOTE)
        if remote is not None:
            branch = self.create_branch_ex(name, remote)
            logging.info(f"Setup remote tracking: {branch.branch_name} -> {remote.branch_name}")
            branch.upstream = remote
            return branch

        # create branch with current head as start point
        if create:
            return self.create_branch_ex(name)

        raise NoBranchError

    def create_branch_ex(self, name: str, start_point: str | git.Branch | None = None) -> git.Branch:
        """Create a new branch.

        Creates a new branch with the given name and start point.
        In contrast to pygit's API this function takes a Branch object
        and converts it to a commit that is required by pygit's `create_branch`.

        Warning:
            This does not check if the branch already exists.

        Args:
            name (str):
                Name of the branch to be created.
            start_point (str | git.Branch | None, optional):
                Start point of the new branch.
                If omitted the current local HEAD is used.
                Defaults to None.

        Returns:
            git.Branch:
                The newly created branch.
        """
        if start_point is None:
            start_point = self.head.shorthand
        elif isinstance(start_point, git.Branch):
            start_point = start_point.branch_name
        commit, _ = self.resolve_refish(start_point)

        logging.info(f"Creating new branch: {name}")
        logging.info(f"Start point: {start_point} ({str(commit.id)[:7]})")
        return self.create_branch(name, commit)

    def list_worktrees_ex(self) -> list[git.Worktree]:
        """List worktrees.

        Reduces the two step process into a single function call.
        Usually you would have to iterating the list of worktree names
        and turning them into worktree objects.

        Returns:
            list[git.Worktree]:
                List of all existing worktrees within the current repository.
        """
        return [self.lookup_worktree(name) for name in self.list_worktrees()]

    def list_worktrees_ex2(self) -> dict[str, git.Worktree]:
        """High-level function to create a dict of worktree.

        The key of the dictionary is the branch name represented by the worktree.

        Returns:
            dict[str, git.Worktree]:
                Dictionary of the existing worktrees.
                The key of the dictionary is the branch name represented by the worktree.
        """
        return {GitRepository(worktree.path).head.shorthand: worktree for worktree in self.list_worktrees_ex()}

    def lookup_worktree_ex(self, name: str) -> git.Worktree:
        """Get the worktree that represents a specific branch.

        This uses the `list_worktrees_ex2` function
        and then uses the access operator to get the worktree for the given branch name.

        Args:
            name (str):
                Name of the branch.

        Returns:
            git.Worktree:
                Worktree that represents the branch in the local file system.
        """
        return self.list_worktrees_ex2()[name]


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
@click.argument("branch", type=str)
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
    repository = GitRepository()
    for name, worktree in repository.list_worktrees_ex2().items():
        click.echo(f"{name} -> {worktree.path}")


@main.command("shell")
@common_decorators
@click.argument("name", type=str)
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

    from pygwt.misc import Shell

    repository = GitRepository()
    try:
        # check if the worktree already exists...
        worktree = repository.lookup_worktree_ex(name)
        if temporary:
            logging.debug(f"{name} already exists. Disabling `temporary` option")
            temporary = False
    except KeyError:
        if create:
            path = repository.root.joinpath(name).resolve()
            path.parent.mkdir(parents=True, exist_ok=True)

            branch = repository.get_branch(name, create=True)
            worktree_name = hashlib.sha1(name.encode()).hexdigest()  # noqa: S324 - SHA1 is sufficient...
            worktree = repository.add_worktree(worktree_name, path.as_posix(), branch)
        else:
            logging.error(f"{name} is not an existing worktree")  # noqa: TRY400 - I don't want to log the exception.
            sys.exit(1)

    Shell.detect().spawn(worktree.path)

    if create and temporary:
        logging.info(f"Removing temporary worktree: {name}")
        shutil.rmtree(worktree.path)
        worktree.prune()


if __name__ == "__main__":
    main()
