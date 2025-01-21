"""Abstraction layer for pygit2."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, NamedTuple

import pygit2

if TYPE_CHECKING:
    from os import PathLike


class NoRepositoryError(FileNotFoundError):
    """Exceptions raised by GitRepository, when no repository was discoverd."""


class NoBranchError(FileNotFoundError):
    """Exception raised by GitRepository, when one of the high-level function could not find a branch."""


class NoWorktreeError(KeyError):
    """Exception raised if a worktree does not exists."""


class FakeWorktree(NamedTuple):
    """
    A fake worktree object.

    A pygit2.Worktree can not be instantiated by us.
    Because a regular repository is a Worktree as well,
    a surrogate is required.
    """

    name: str
    path: str


class Repository(pygit2.Repository):
    """High-level abstraction for pygit's Repository class."""

    def __init__(self, path: str | Path | None = None) -> None:
        """Create new instance.

        This will use the `discover_repository` method
        and initialize the underlying super class with that.

        Args:
            path (str | Path | None, optional):
                Path of a repository.
                If omitted, the current working directory will be used.
                Defaults to None.

        Raises:
            NoRepositoryError:
                If no repository could be discovered in the given path.
        """
        if path is None:
            path = pygit2.discover_repository(Path.cwd().as_posix())

        if path is None:
            msg = "No repository detected..."
            raise NoRepositoryError(msg)
        super().__init__(Path(path).as_posix())

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

    def get_branch(
        self,
        name: str,
        *,
        start_point: str | pygit2.Branch | None = None,
        create: bool = False,
    ) -> pygit2.Branch:
        """Abstraction function that's suppose to emulate the behavior of `git branch`.

        This function will first look for a local branch with the given name
        and return it if it exists.

        If not no local branch was found it will look for a remote branch (origin only)
        with the given name.
        When successful a new local branch with the same name will be created,
        setup to track the remote counterpart and returned.

        If None of the above cases where successful
        and `create` is set to true a new local branch will be created.
        The newly created branch will be based on the current local HEAD
        or on `start_point` if given.

        Args:
            name (str):
                Name of the desired branch.
            start_point (str | pygit2.Branch | None, optional):
                If create is set,
                this argument is used
                for determining the start point of the new branch.
                Defaults to None.
            create (bool, optional):
                If set to `True` and no local branch with the given name exists,
                a new branch will be created.
                Defaults to False.

        Raises:
            NoBranchError:
                If neither local nor remote where found
                and create wasn't set either.

        Returns:
            pygit2.Branch:
                The existing or newly created local branch.
        """
        logging.debug(f"Lookup local branch: {name}")
        # look for already existing local branch
        branch = self.lookup_branch(name, pygit2.enums.BranchType.LOCAL)
        if branch is not None:
            logging.debug(f"Found local branch: {name}")
            return branch

        # look for a remote branch. If one is found create a local tracking branch.
        logging.debug("No local branch found. Looking for remote branch.")
        remote = self.lookup_branch(f"origin/{name}", pygit2.enums.BranchType.REMOTE)
        if remote is not None:
            branch = self.create_branch_ex(name, remote)
            logging.debug(f"'{branch.branch_name}' set up to track '{remote.branch_name}'")
            branch.upstream = remote
            return branch

        # create branch with current head as start point
        if create:
            return self.create_branch_ex(name, start_point)

        raise NoBranchError

    def create_branch_ex(self, name: str, start_point: str | pygit2.Branch | None = None) -> pygit2.Branch:
        """Create a new branch.

        Creates a new branch with the given name and start point.
        In contrast to pygit's API this function takes a Branch object
        and converts it to a commit that is required by pygit's `create_branch`.

        Warning:
            This does not check if the branch already exists.

        Args:
            name (str):
                Name of the branch to be created.
            start_point (str | pygit2.Branch | None, optional):
                Start point of the new branch.
                If omitted the current local HEAD is used.
                If the local head does not exists,
                the remote HEAD will be used.
                Defaults to None.

        Returns:
            pygit2.Branch:
                The newly created branch.
        """
        commit: pygit2.Commit
        if start_point is None:
            try:
                reference = self.lookup_reference_dwim("HEAD")
            except KeyError:
                # This is a rare case that only happens,
                # when executed in a bare clone
                # and the branch HEAD refers to
                # hasn't yet been checked out.
                reference = self.lookup_reference_dwim("origin/HEAD")
            commit = reference.peel(pygit2.enums.ObjectType.COMMIT)  # type: ignore[call-overload]
        elif isinstance(start_point, str):
            commit, _ = self.resolve_refish(start_point)
        elif isinstance(start_point, pygit2.Branch):
            commit = start_point.peel(pygit2.enums.ObjectType.COMMIT)  # type: ignore[call-overload]
        else:
            msg = f"Invalid start point: {start_point}"
            raise ValueError(msg)

        logging.debug(f"Creating branch '{name}' (HEAD is at {str(commit.id)[:7]})")
        return self.create_branch(name, commit)

    def list_worktrees_ex(self) -> list[pygit2.Worktree]:
        """List worktrees.

        Reduces the two step process into a single function call.
        Usually you would have to iterating the list of worktree names
        and turning them into worktree objects.

        Returns:
            list[pygit2.Worktree]:
                List of all existing worktrees within the current repository.
        """
        return [self.lookup_worktree(name) for name in self.list_worktrees()]

    def list_worktrees_ex2(self) -> dict[str, pygit2.Worktree]:
        """High-level function to create a dict of worktree.

        The key of the dictionary is the branch name represented by the worktree.

        Returns:
            dict[str, pygit2.Worktree]:
                Dictionary of the existing worktrees.
                The key of the dictionary is the branch name represented by the worktree.
        """
        return {self.open_worktree(worktree).head.shorthand: worktree for worktree in self.list_worktrees_ex()}

    def lookup_worktree_ex(self, name: str) -> pygit2.Worktree:
        """Get the worktree that represents a specific branch.

        This uses the `list_worktrees_ex2` function
        and then uses the access operator to get the worktree for the given branch name.

        Args:
            name (str):
                Name of the branch.

        Returns:
            pygit2.Worktree:
                Worktree that represents the branch in the local file system.
        """
        worktree = self.list_worktrees_ex2().get(name, None)
        if worktree is None:
            msg = f"No matching worktree for branch '{name}'"
            raise NoWorktreeError(msg)
        return worktree

    def open_worktree(self, worktree: pygit2.Worktree) -> Repository:
        """
        Open the given worktree as a Repository.

        This function assumes that the root of the repository
        contains a '.git' directory,
        which in turn contains a 'worktrees' directory
        that holds the worktree metadata.

        Args:
            worktree (pygit2.Worktree):
                The worktree that shall be opened.

        Returns:
            Repository:
                A new repository instance
                that represents the given worktree.
        """
        return Repository(self.root.joinpath(".git", "worktrees", worktree.name))

    def as_worktree(self) -> pygit2.Worktree | FakeWorktree:
        """
        Get a Worktree for the current repository.

        This functions check if a worktree for the Repository exists,
        if that's the case a Worktree instance is returned.
        If not it's assumed that the Repository refers to the current root
        of the clone.
        Which results in a FakeWorktree being returned.

        In case of the FakeWorktree the name contains the branch name
        instead of the Worktree directory name.

        Returns:
            pygit2.Worktree | FakeWorktree:
                Instance of a worktree representation.
        """
        try:
            return self.lookup_worktree_ex(self.head.shorthand)
        except NoWorktreeError:
            return FakeWorktree(self.head.shorthand, self.root.as_posix())

    def get_worktree(
        self,
        name: str,
        *,
        create: bool = False,
        start_point: str | None = None,
        dest: str | PathLike | None = None,
    ) -> pygit2.Worktree | FakeWorktree:
        """
        Get and create it if necessary.

        Args:
            name (str):
                Name of the branch checked out or to checkout within the worktree.
                If no branch with the the given name exists
                a new one is created.
            create (bool, optional):
                If set, create worktree if does not exists yet.
                Defaults to False.
            start_point (str | None, optional):
                ref'ish start point to use when a new branch is created.
                Defaults to None.
            dest (str | PathLike | None, optional):
                Destination directory for the new worktree.
                If omitted the '<repo root>/<name>' is used.
                Defaults to None.

        Returns:
            pygit2.Worktree | FakeWorktree:
                The worktree existing or newly created worktree.

        Raises:
            NoWorktreeError:
                If create wasn't set and the worktree does not exist.
        """
        import hashlib

        # make sure that the given name does not refer
        # to a non-bare root
        root = Repository(self.root)
        if not root.is_bare and root.head.shorthand == name:
            logging.debug(f"'{name}' already checked out at '{self.root}'.")
            return root.as_worktree()

        try:
            # check if the worktree already exists...
            worktree = self.lookup_worktree_ex(name)
        except NoWorktreeError:
            if create:
                dest = self.root.joinpath(name).resolve() if dest is None else Path(dest)
                dest.parent.mkdir(parents=True, exist_ok=True)
                logging.info(f"Preparing new worktree: {name} -> {dest}")

                branch = self.get_branch(name, create=True, start_point=start_point)
                worktree_name = hashlib.sha1(name.encode()).hexdigest()  # noqa: S324 - SHA1 is sufficient...
                logging.info(f"Checking out '{branch.branch_name}' (HEAD: {str(branch.peel(None).id)[:7]})")
                worktree = self.add_worktree(worktree_name, dest.as_posix(), branch)
            else:
                raise

        if worktree.is_prunable:
            logging.warning(f"'{name}' worktree marked as prunable.")
            self.restore_worktree(worktree)

        return worktree

    def repair_worktree(self, worktree: pygit2.Worktree) -> None:
        """
        Repair a worktree.

        This will restore the worktrees directory
        and the '.git' file that points to the repo metadata.
        """
        path = Path(worktree.path)
        repo = self.open_worktree(worktree)
        logging.info(f"Repairing worktree: '{path}'")

        # restore potentially deleted directory
        path.mkdir(parents=True, exist_ok=True)
        path.joinpath(".git").write_text(f"gitdir: {repo.path}")

    def restore_worktree(self, worktree: pygit2.Worktree) -> None:
        """
        Restore worktree.

        Repair the given worktree
        and call checkout to restore the files.
        """
        if not worktree.is_prunable:
            return

        repo = self.open_worktree(worktree)
        repo.repair_worktree(worktree)
        repo.checkout()

    def list_local_branches(self) -> list[pygit2.Branch]:
        """Get a list of all local branches."""
        return [self.branches[name] for name in self.branches.local]

    def list_remote_branches(self) -> list[pygit2.Branch]:
        """Get a list of all remote branches."""
        return [self.branches[name] for name in self.branches.remote]
