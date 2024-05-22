# PyGWT - Python Git Worktree

A CLI tool that's suppose to ease the `git worktree` workflow.

## Motivation

I just recently learned about `git worktree`
and found it very intresting.
While searching the internet
I found two ways to work with it:

1. Use a bare clone and create directories for the different worktrees within that clone.
1. Use a regular clone and create temp directories for the different worktrees.

I tried both options
and both of them either felt wrong
or had some major flaws e.g:
With a regular bare clone
my Git status shell integration wasn't able to detect changes,
because a bare clone does not hold any information
about the remote branches.
(At least that's what I figured out, with my limited knowledge)

After a lot of trial and error I figured out a way
to configure a bare clone to work exactly how I wanted it.
But to get there I'd had to run 4 commands only to get an empty clone.
The command for creating worktree checkout
with automated remote tracking was also very cumbersome.

That's when I decided that I want a script or tool that hides this complexity.
I found Linux shell scripts[^1] that did some of the heavy lifting.
But since I work on Windows and Linux I needed something that works on both platforms.
Hence I decided to create my own tool,
in a scripting language that is available on all platforms.

## Prerequisites

- Python >= 3.10
- *optional*: pipx

## Installation:

```shell
pipx install git+https://github.com/Bubichoo-Teitichoo/pygwt
```

## Usage

> [!NOTE]
>
> Because the project is work in progress
> the CLI may be subject to change.
> So take everything with a grain of salt
> and consult the build in help.

### `pygwt install alias`

Installs a Git alias for seemless usage.

| Arguments | Argument Type | Default  |                                                     Description                                                      |
| :-------: | :-----------: | :------: | :------------------------------------------------------------------------------------------------------------------: |
|   name    |  positional   |   `wt`   |                                                  Name of the alias                                                   |
|   scope   |    keyword    | `global` | The scope of the alias: [`local`][gc-local], [`global`][gc-global], [`system`][gc-system], [`worktree`][gc-worktree] |

### `pygwt clone`

Create a new directory
and initialize it for a worktree based workflow.

> \[!NOTE\]
>
> After cloning the newly create directory will only contain a *.git* directory
> which contains the usual git related files.
>
> Use `pygwt add` to create a checkout.

| Arguments | Argument Type |          Default          |                                                                   Description                                                                   |
| :-------: | :-----------: | :-----------------------: | :---------------------------------------------------------------------------------------------------------------------------------------------: |
|    url    |  positional   |             -             |                                The repository that shall be cloned. (URL, Path what ever works with `git clone`)                                |
|   dest    |  positional   | current working directory | The target directory in which the repository is to be cloned.<br>If omitted the tool will inferre the target directory, similar to `git clone`. |

### `pygwt add`

Add a new worktree checkout for the given branch.
If the given branch name matches a remote branch
the checkout will automatically track the remote branch.

|  Arguments  | Argument Type | Default |                                                  Description                                                   |
| :---------: | :-----------: | :-----: | :------------------------------------------------------------------------------------------------------------: |
|   branch    |  positional   |    -    |                                     The branch that is to be checked out.                                      |
| start-point |  positional   |  None   |                         The base of the new branch. If omitted it's the current HEAD.                          |
|    dest     |    keyword    |  None   | The destination of the checkout.<br>If omitted the destination is the current working directory + branch name. |

### `pygwt list`

List all available worktrees.

### `pygwt shell`

Spawn a new shell within the selected worktree.

Detect the current shell,
the command is executed in
and spawn a new instance within the directory
of the worktree defined by name.

If the worktree does not exist yet,
a new one can be created using the `--create` flag.
If the `--create` flag is set
the command will behave similar to `git switch`.

1. The script will check if a branch with the given name exists.
    A new worktree will be created, that contains the checkout of the branch.
1. If no local branch exists but a remote, that matches the name,
    a new local branch that tracks the remote one is created
    and checked out within a new worktree.
1. If None of the above apply a new branch will be created,
    that forks the current `HEAD`.

> [!NOTE]
> New worktrees are always created in the root of the repository clone.

|  Arguments  | Argument Type | Default |                                                  Description                                                   |
| :---------: | :-----------: | :-----: | :------------------------------------------------------------------------------------------------------------: |
|    name     |   positional  |    -    | The name of the branch. |
|  c / create |     flag      |  false  | If set and the given branch has no worktree yet. A new worktree will be created. |
|  t / temporary | flag | false | If set along with `create` the worktree will be deleted and pruned when the shell is exited. |

## Roadmap - v1.0.0

- [ ] `switch` command that changes worktrees in the current shell
- [x] `list` command
- [ ] replace Git CLI calls with libgit2
- [ ] autocompletion of branch names...
    - [ ] for Windows Powershell
    - [x] for Bash
    - [x] for Zsh
- [ ] TBC...

[gc-global]: https://git-scm.com/docs/git-config#Documentation/git-config.txt---global
[gc-local]: https://git-scm.com/docs/git-config#Documentation/git-config.txt---local
[gc-system]: https://git-scm.com/docs/git-config#Documentation/git-config.txt---system
[gc-worktree]: https://git-scm.com/docs/git-config#Documentation/git-config.txt---worktree
[^1]: https://github.com/yankeexe/git-worktree-switcher
