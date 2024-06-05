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

## Installation

```shell
pipx install git+https://github.com/Bubichoo-Teitichoo/pygwt
```

## Roadmap - v1.0.0

- [ ] `switch` command that changes worktrees in the current shell
    - [x] for Windows Powershell
    - [ ] for Bash
    - [ ] for Zsh
- [x] `list` command
- [ ] replace Git CLI calls with libgit2
- [x] autocompletion of branch names...
    - [x] for Windows Powershell
    - [x] for Bash
    - [x] for Zsh
- [ ] TBC...

[^1]: <https://github.com/yankeexe/git-worktree-switcher>
