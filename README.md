# git-twig - `git worktree` as it should be.

Working with `git worktree` can be a bit finicky at time.
`git-twig` aims to make worktrees a first class citizens,
similar to branches.

Using it's shell integration, `git-twig` makes switching between worktrees
as easy as `git twig switch ...`.

![Demo](./docs/git-twig-demo.gif)

## Prerequisites

- Python >= 3.10

## Installation

```shell
# installation with pipx
pipx install git+https://github.com/Bubichoo-Teitichoo/git-twig
# installation with uv
uv tool install git+https://github.com/Bubichoo-Teitichoo/git-twig
```

## Usage

see [CLI reference](https://bubichoo-teitichoo.github.io/pygwt/latest/cli/)

### Shell Completion/Integration

*git-twig* has supports for the following shells:

- powershell/pwsh
- zsh
- bash

> [!NOTE]
> The `git-twig init` command is able to detect your current shell.
> If this detection, for whatever reason, is not working,
> add the name of your shell as and additional argument
> e.g. `git-twig zsh`.

#### zsh

To add shell completion and integration to zsh,
add the following line to you *.zshrc*.

```shell
eval "$(git-twig init)"
```

#### bash

To add shell completion and integration to bash,
add the following line to you *.bashrc*.

```shell
eval "$(git-twig init)"
```

#### powershell

To add shell completion and integration to powershell,
add the following line to you `$PROFILE`.

```shell
@(& git-twig init) -join "`n" | Invoke-Expression
```
