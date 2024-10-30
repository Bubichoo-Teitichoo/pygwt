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

import pygwt.log
from pygwt import git
from pygwt.completions import PowershellComplete  # noqa: F401 - required to enable powershell completions
from pygwt.misc import Shell


# def git_cmd(cmd: str, *args: str, check: bool = True, capture: bool = True) -> subprocess.CompletedProcess[str]:
#     """
#     Execute a git command, with the given arguments.
#
#     Returns:
#         subprocess.CompletedProcess[str]:
#             The result of the command.
#     """
#     logging.debug(f"Executing: git {cmd}")
#     logging.debug(f"Arguments: {args}")
#     return subprocess.run(["git", cmd, *args], check=check, capture_output=capture, text=True, encoding="UTF-8")  # noqa: S603, S607
#
#
# T = TypeVar("T", bound=Callable)
#
#
# def common_decorators(func: T) -> T:
#     """
#     Decorator that adds "global" options and other modifications to the click commands.
#
#     The Decorator applies the following option:
#
#     - help option with `-h` and `--help` to trigger it
#         opposed to the `--help` that's added by default.
#     - version option
#
#     The Decorator applies the following additional modifiers:
#
#     - Loguru catcher that catches and pretty print exceptions
#         and exits afterwards.
#     """
#     func = click.help_option("-h", "--help")(func)
#     func = click.version_option()(func)
#     return pygwt.logging.catcher()(func)
#
#
# def all_branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
#     """Function that creates a list of branches for shell completion."""
#     repository = git.Repository()
#     return [branch for branch in repository.branches if branch.startswith(incomplete)]
#
#
# def branch_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:  # noqa: ARG001
#     """Function that creates a list of branches for shell completion."""
#     repository = git.Repository()
#     branches = {}
#     for branch in repository.list_remote_branches():
#         if branch.branch_name.endswith("HEAD"):
#             continue
#         name = Path(branch.branch_name).relative_to(branch.remote_name).as_posix()
#         branches[name] = CompletionItem(name, help=branch.branch_name)
#
#     for branch in repository.list_local_branches():
#         branches[branch.branch_name] = CompletionItem(branch.branch_name)
#
#     return [completion for name, completion in branches.items() if name.startswith(incomplete)]
#
#
# def worktree_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[CompletionItem]:
#     """Create list of worktree names matching the given incomplete name."""
#     repository = git.Repository()
#     worktrees = [
#         CompletionItem(name, help=worktree.path)
#         for name, worktree in repository.list_worktrees_ex2().items()
#         if name.startswith(incomplete)
#     ]
#     if ctx.params.get("create", False):
#         return branch_shell_complete(ctx, param, incomplete) + worktrees
#     return worktrees
#
#
# def repositories_shell_complete(ctx: click.Context, param: click.Parameter, incomplete: str) -> list[str]:  # noqa: ARG001
#     """Function that creates a list of branches for shell completion."""
#     config = pygit2.Config.get_global_config()
#
#     try:
#         registry = config["wt.registry"].split(",")
#     except KeyError:
#         registry = []
#     return [path for path in registry if path.startswith(incomplete)]
#
#
# @main.command("switch")
# @common_decorators
# @click.argument("name", type=str, shell_complete=worktree_shell_complete)
# @click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
# @click.option(
#     "-c",
#     "--create",
#     type=bool,
#     is_flag=True,
#     default=False,
#     show_default=True,
#     help="Create the worktree if it does not yet exists.",
# )
# def worktree_switch(name: str, start_point: str, *, create: bool) -> None:
#     """Switch to a different worktree.
#
#     > [!NOTE]
#     > This requires the Shell hooks included in the completion scripts.
#     > Otherwise it will just print the worktree path
#
#     Under the hood worktrees are given an abstract name.
#     With this command [NAME] is the branch name the worktree represents.
#
#     This command works similar to `git switch` for branches.
#     If a worktree does not exist the 'create'-flag is required to create a new one.
#
#     The create flag will also create a new branch,
#     if no branch for the given name could be found.
#     If [START-POINT] is omitted,
#     the current *HEAD* is used.
#
#     If name is `-` you will switch to the previous directory.
#     """
#     repository = git.Repository()
#     pcwd = Path.cwd().as_posix()
#     if name == "-":
#         try:
#             last = repository.config["wt.last"]
#             click.echo(last)
#         except KeyError:
#             logging.error("No last worktree/branch to switch to...")  # noqa: TRY400
#             click.echo(".")
#             sys.exit(1)
#     else:
#         worktree = repository.get_worktree(name, create=create, start_point=start_point)
#         repository.config["wt.last"] = Path.cwd().as_posix()
#         click.echo(worktree.path)
#     repository.config["wt.last"] = pcwd
#
#
#
#
# @main.command("shell")
# @common_decorators
# @click.argument("name", type=str, shell_complete=worktree_shell_complete)
# @click.argument("start_point", type=str, default=lambda: None, shell_complete=all_branch_shell_complete)
# @click.option(
#     "-c",
#     "--create",
#     type=bool,
#     is_flag=True,
#     default=False,
#     show_default=True,
#     help="Create the worktree if it does not yet exists.",
# )
# @click.option(
#     "-d",
#     "--delete",
#     type=bool,
#     is_flag=True,
#     default=False,
#     show_default=True,
#     help="Delete the checkout after exiting the shell.",
# )
# def worktree_shell(name: str, start_point: str | None, *, create: bool, delete: bool) -> None:
#     """Spawn a new shell within the selected worktree.
#
#     > [!WARNING]
#     > This command spawns a new shell,
#     > which may result in some unexpected side-effects.
#     > Consider using `pygwt switch` instead.
#
#     Detect the current shell,
#     the command is executed in
#     and spawn a new instance within the directory
#     of the worktree defined by [NAME].
#
#     If the branch, defined by [NAME],
#     does not exist and the create flag is set,
#     a new branch will be created.
#     If [START_POINT] is omitted
#     the current HEAD will be used as a start point.
#     """
#     import os
#
#     from pygwt.misc import Shell
#
#     logging.warning("This command may have some unexpected side-effects.")
#     logging.warning("It's recommended to use 'pygwt switch' instead")
#
#     repository = git.Repository()
#     try:
#         worktree = repository.get_worktree(name, create=create, start_point=start_point)
#     except git.NoWorktreeError as exception:
#         logging.error(str(exception).strip('"'))  # noqa: TRY400 - I don't want to log the exception.
#         logging.info("Use the '-c'/'--create' flag to create a new worktree.")
#         sys.exit(1)
#
#     # If we're inside a bare checkout,
#     # Git will set GIT_DIR when executing an alias.
#     # Because of that Git will think that we're on the HEAD branch,
#     # if in fact we're within a worktree.
#     git_dir_env = None
#     if "GIT_DIR" in os.environ:
#         git_dir_env = os.environ.pop("GIT_DIR")
#     Shell.detect().spawn(worktree.path)
#     if git_dir_env is not None:
#         os.environ["GIT_DIR"] = git_dir_env
#
#     if create and delete and not isinstance(worktree, git.FakeWorktree):
#         logging.info(f"Removing temporary worktree: {name}")
#         shutil.rmtree(worktree.path)
#         worktree.prune()


def main() -> None:
    from pygwt.cli import commands
    from pygwt.cli.loader import CLIBuilder

    option = pygwt.log.option("-l", "--log")

    builder = CLIBuilder()
    group = builder.build(commands)
    option(group)
    group()


if __name__ == "__main__":
    main()
