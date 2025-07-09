# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [0.5.0](https://github.com/Bubichoo-Teitichoo/pygwt/releases/tag/0.5.0) - 2025-07-09

<small>[Compare with 0.4.0](https://github.com/Bubichoo-Teitichoo/pygwt/compare/0.4.0...0.5.0)</small>

### Features

- Add commands for quick switching between repositories ([2e7e0e5](https://github.com/Bubichoo-Teitichoo/pygwt/commit/2e7e0e5c8ab3b34a6cf96ebd505279ce0ab5674d) by Philipp Krüger).
- Enable back and forth switching ([686bc7e](https://github.com/Bubichoo-Teitichoo/pygwt/commit/686bc7e21f01c5c5ca730d4821cb4d4ee3167ab7) by Philipp Krüger).

### Bug Fixes

- Restore powershell integration ([92300d0](https://github.com/Bubichoo-Teitichoo/pygwt/commit/92300d01bf100aa587ccf397b1f9de342d1057ca) by Philipp Krüger).
- Add repository root not '.git' directory to registroy when using 'git wt clone' ([a7549d2](https://github.com/Bubichoo-Teitichoo/pygwt/commit/a7549d2a3d3e4e2ba1ad450a1017f4767224e55b) by Philipp Krüger).
- Use worktree paths instead of branch names for 'git wt remove' completions ([630257c](https://github.com/Bubichoo-Teitichoo/pygwt/commit/630257c6fd45d9bd0184fdc447e8a2298b504a3b) by Philipp Krüger).
- Use custom completion for 'git-wt add' ([925aa9f](https://github.com/Bubichoo-Teitichoo/pygwt/commit/925aa9f16fd6e6500c52181d853996c3313af246) by Philipp Krüger).
- Properly create new branches ([9c440b0](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9c440b0acff038d0105fb993c184836fcac850c8) by Philipp Krüger).
- Redirect stdout of git cli invocations to stderr ([1db9ce8](https://github.com/Bubichoo-Teitichoo/pygwt/commit/1db9ce81fe0319cb6d19c4266cd90a72d6279431) by Philipp Krüger).
- Only run cd command if git-wt didn't fail ([04aaec6](https://github.com/Bubichoo-Teitichoo/pygwt/commit/04aaec67126d735ef7b99393296f4a7f826eda14) by Philipp Krüger).
- Remove debug output from zsh completion script ([72f40c2](https://github.com/Bubichoo-Teitichoo/pygwt/commit/72f40c2c1ac0ca23ba6cb2dd4a6c3c024cbaba1e) by Philipp Krüger).
- Re-add _git-wt method to zsh init script ([8bbf9c6](https://github.com/Bubichoo-Teitichoo/pygwt/commit/8bbf9c6cc2645c6b256c518ba6899f28c84085e4) by Philipp Krüger).
- Remove '.git' suffix from destination ([e5dad4d](https://github.com/Bubichoo-Teitichoo/pygwt/commit/e5dad4dea3db10b3457c145f6fd5a623fda6b3dd) by Philipp Krüger).

### Code Refactoring

- Delete empty parent directories when removing a worktree ([ef9e788](https://github.com/Bubichoo-Teitichoo/pygwt/commit/ef9e788508de956c05d55f9885cb171df817f397) by Philipp Krüger).
- Improve printed worktree list ([b850e6b](https://github.com/Bubichoo-Teitichoo/pygwt/commit/b850e6b90db46c55d139bc54981cb72be120f0a1) by Philipp Krüger).
- Reduce complexity by removing pygit2 ([ec97d02](https://github.com/Bubichoo-Teitichoo/pygwt/commit/ec97d02968255872f39b93ecc94e378c05f79b04) by Philipp Krüger).
- Use contextlib to make pushd much more lightweight ([c455b36](https://github.com/Bubichoo-Teitichoo/pygwt/commit/c455b36310c2f29579b09ebca34bac9bbc2d0098) by Philipp Krüger).
- Use git CLI when creating new worktrees ([e5cdfa8](https://github.com/Bubichoo-Teitichoo/pygwt/commit/e5cdfa8da200ee8b7e5283efaf6059c58b09e3f0) by Philipp Krüger).
- Use `git.execute` when removing worktrees ([475275f](https://github.com/Bubichoo-Teitichoo/pygwt/commit/475275f06d0fa340d43828317d29b709f19ff9b4) by Philipp Krüger).
- Use git.execute function instead of subprocess ([b37c445](https://github.com/Bubichoo-Teitichoo/pygwt/commit/b37c445ecc4d2d01f222ca91d1b2b7b8285bf8a5) by Philipp Krüger).
- Use git CLI when creating a worktree ([e885eaf](https://github.com/Bubichoo-Teitichoo/pygwt/commit/e885eafefe3d9476a3903ac03a77c9f069627e14) by Philipp Krüger).
- Use git CLI when cloning a repository ([5c5433c](https://github.com/Bubichoo-Teitichoo/pygwt/commit/5c5433cfd7bef4ecba4fb1df46dc5fabf6085246) by Philipp Krüger).
- Add execute methode to git module ([6632345](https://github.com/Bubichoo-Teitichoo/pygwt/commit/6632345ea0fd5e0e39fc7aed4cd3b4674552f1e5) by Philipp Krüger).
- Fix linter findings ([61a145b](https://github.com/Bubichoo-Teitichoo/pygwt/commit/61a145b2dd5c5df750a53518d303715f18e458e3) by Philipp Krüger).
- Replace install commands with init commands ([95e58f5](https://github.com/Bubichoo-Teitichoo/pygwt/commit/95e58f54ea78863e96671bc80b4a6521f8003603) by Philipp Krüger).
- Move commands and utility functions into own modules ([1dfcb4d](https://github.com/Bubichoo-Teitichoo/pygwt/commit/1dfcb4dceddaa17e7515270faccf850c8679c6dd) by Philipp Krüger).
- Remove redundant pygit2 imports ([451231d](https://github.com/Bubichoo-Teitichoo/pygwt/commit/451231dcad5be8ccfed1485c81bb4f8c14191acc) by Philipp Krüger).

## [0.4.0](https://github.com/Bubichoo-Teitichoo/pygwt/releases/tag/0.4.0) - 2024-06-07

<small>[Compare with 0.3.1](https://github.com/Bubichoo-Teitichoo/pygwt/compare/0.3.1...0.4.0)</small>

### Features

- Add 'switch' hook for bash ([4212f56](https://github.com/Bubichoo-Teitichoo/pygwt/commit/4212f56e8d592a42226102071cea07f3943f7f10) by Philipp Krüger).
- Add 'switch' hook for zsh ([5b1327a](https://github.com/Bubichoo-Teitichoo/pygwt/commit/5b1327a69f5ed664aea1257fb1c860b886737df5) by Philipp Krüger).

### Code Refactoring

- Shorten 'remove' and 'list' command ([254ed0e](https://github.com/Bubichoo-Teitichoo/pygwt/commit/254ed0e9d54fa1dbee383b760fcfb028321a4645) by Philipp Krüger).

## [0.3.1](https://github.com/Bubichoo-Teitichoo/pygwt/releases/tag/0.3.1) - 2024-06-06

<small>[Compare with 0.3.0](https://github.com/Bubichoo-Teitichoo/pygwt/compare/0.3.0...0.3.1)</small>

### Bug Fixes

- Use incomplete in completions ([561eb06](https://github.com/Bubichoo-Teitichoo/pygwt/commit/561eb06fc17fcc602cbe761fe8e3750c292e2993) by Philipp Krüger).

## [0.3.0](https://github.com/Bubichoo-Teitichoo/pygwt/releases/tag/0.3.0) - 2024-06-05

<small>[Compare with first commit](https://github.com/Bubichoo-Teitichoo/pygwt/compare/8085ac79b808ff299abb102979b4639acee940d3...0.3.0)</small>

### Features

- Improve completion for start points ([b99cfd8](https://github.com/Bubichoo-Teitichoo/pygwt/commit/b99cfd8da3ce2a7658f15b1ea4bf09bdbe903b1d) by Philipp Krüger).
- Add 'switch' command and powershell proxy ([a5c00b1](https://github.com/Bubichoo-Teitichoo/pygwt/commit/a5c00b1b17cc3fa2d02e0662ac97f65e065e9e36) by Philipp Krüger).
- Add 'remove' command ([4bb4de9](https://github.com/Bubichoo-Teitichoo/pygwt/commit/4bb4de9af6f1d2bc0d4e03b6e13a6354d354c4fd) by Philipp Krüger).
- Add completion function for worktree names ([9d6135c](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9d6135cace948dd787898a6a7931c466cadf43de) by Philipp Krüger).
- Add powershell completions ([853ac42](https://github.com/Bubichoo-Teitichoo/pygwt/commit/853ac426c88f0a12feeeceb9df66a9d346fd3f38) by Philipp Krüger).
- Add start point argument to get_branch function ([be2c4a9](https://github.com/Bubichoo-Teitichoo/pygwt/commit/be2c4a920b72cf5cf759456cd3cbbcbf9a6e8435) by Philipp Krüger).
- Add bash shell completions ([9ce79a9](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9ce79a9040b647becf16168de92e4514a851f53d) by Philipp Krüger).
- Add ZSH completions ([1ccabbc](https://github.com/Bubichoo-Teitichoo/pygwt/commit/1ccabbceb0944ce38932de6a125d4b71afc6471f) by Philipp Krüger).
- Enable switch for root worktree if non-bare ([feaadfb](https://github.com/Bubichoo-Teitichoo/pygwt/commit/feaadfb80abd594ac010cef88b9894c9c0e91acc) by Philipp Krüger).
- Add as_worktree function to Repository ([d141b37](https://github.com/Bubichoo-Teitichoo/pygwt/commit/d141b373da7d0a56b956ec2bb1f80579207c3e44) by Philipp Krüger).
- List non-bare repository root ([2f37cea](https://github.com/Bubichoo-Teitichoo/pygwt/commit/2f37cea46f216d21881473422ef44b04d33c73a6) by Philipp Krüger).
- Add open_worktree function ([b48b166](https://github.com/Bubichoo-Teitichoo/pygwt/commit/b48b1665d24dbf19b43275c4c20f644d33411855) by Philipp Krüger).
- Add support for Path objects to Repository constructor ([0b817ae](https://github.com/Bubichoo-Teitichoo/pygwt/commit/0b817aeaae83bae39264538f10d69de3e35a4faf) by Philipp Krüger).
- Log when creating a new worktree ([a3f539f](https://github.com/Bubichoo-Teitichoo/pygwt/commit/a3f539fa8a7b13fe3237b2f47f8b21aba52de939) by Philipp Krüger).
- Always create worktree directories in repository root ([dc291bc](https://github.com/Bubichoo-Teitichoo/pygwt/commit/dc291bc3d3e4f234d56f99ad2b1f2189ed89fb85) by Philipp Krüger).
- Add short version for shell options, rename checkout to create ([d84fb39](https://github.com/Bubichoo-Teitichoo/pygwt/commit/d84fb3930867b71408a14de7af9c96c069ffbac8) by Philipp Krüger).
- Use high-level abstraction functions for branch creation ([61d3bc7](https://github.com/Bubichoo-Teitichoo/pygwt/commit/61d3bc777fc793111b76278b2f6bb0299183fd42) by Philipp Krüger).
- Add high-level functions for worktree operations ([0e687e4](https://github.com/Bubichoo-Teitichoo/pygwt/commit/0e687e43533aff22168f275c98f35d662833cad3) by Philipp Krüger).
- Add high-level get_branch function ([c575ab7](https://github.com/Bubichoo-Teitichoo/pygwt/commit/c575ab7dfda43cb6a8ccaae13d86de4ae5171301) by Philipp Krüger).
- Add high-level abstraction for branch creation ([d2db15f](https://github.com/Bubichoo-Teitichoo/pygwt/commit/d2db15f2b89b9ee2cb7e804921654ecf0465d048) by Philipp Krüger).
- Add support for Windows shells ([3bee3f3](https://github.com/Bubichoo-Teitichoo/pygwt/commit/3bee3f31037897929273a4f60ff2af6956508ad7) by Philipp Krüger).
- Implement PoC for switch command ([047ac13](https://github.com/Bubichoo-Teitichoo/pygwt/commit/047ac137e9205786223ff4e2c1b9acec9ef41ed3) by Philipp Krüger).
- Reduce noise in log output ([edb9814](https://github.com/Bubichoo-Teitichoo/pygwt/commit/edb981449e490218c5b27288f3c2ee5c4c871312) by Philipp Krüger).
- Add command to install a git alias ([9a47311](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9a473110006450d6edc982e0633ed6339c920d36) by Philipp Krüger).
- First draft ([9d68ebb](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9d68ebb72a5a4ee1ea568cdce74c5b54a588dc95) by Philipp Krüger).

### Bug Fixes

- Add powershell completer for pygwt.exe ([db46972](https://github.com/Bubichoo-Teitichoo/pygwt/commit/db46972637a898e904c1e8d4b029a710be4af68e) by Philipp Krüger).
- Only copy completion scripts ([66aa69d](https://github.com/Bubichoo-Teitichoo/pygwt/commit/66aa69d2a063e8166c05d46888a018ee6e7e64a6) by Philipp Krüger).
- Use importlib_resources for backward compatibility ([5fcae6b](https://github.com/Bubichoo-Teitichoo/pygwt/commit/5fcae6b66c6224a038cead85cbba64f99580395d) by Philipp Krüger).
- Only remove GIT_DIR it it exists ([1c01fb9](https://github.com/Bubichoo-Teitichoo/pygwt/commit/1c01fb9a00a75d4431181d1be6e2193661687ae7) by Philipp Krüger).
- Remove GIT_DIR entirely ([812cca5](https://github.com/Bubichoo-Teitichoo/pygwt/commit/812cca55e54368b5981e63751e86adc2d68853a4) by Philipp Krüger).
- Use remote HEAD if local does not exists ([b88aa54](https://github.com/Bubichoo-Teitichoo/pygwt/commit/b88aa54ae4efce5ac4715c3e6a9305f410307497) by Philipp Krüger).
- Remove GIT_DIR variable before spawning shell ([d2ab2a3](https://github.com/Bubichoo-Teitichoo/pygwt/commit/d2ab2a38d108938421a790fa9ff3816b3fa55e19) by Philipp Krüger).
- Start right shell on Windows if command is executed as Git Alias ([41ddaf1](https://github.com/Bubichoo-Teitichoo/pygwt/commit/41ddaf1226fc98d64e8ca19c262f49b495b7b090) by Philipp Krüger).
- Use list_worktree_ex for list command ([2be4cb8](https://github.com/Bubichoo-Teitichoo/pygwt/commit/2be4cb8d01b8d5ae29741b337d1e499af969bb12) by Philipp Krüger).
- Use branch name lookup instead of low level worktree lookup ([9370826](https://github.com/Bubichoo-Teitichoo/pygwt/commit/93708260e897373f62417fbf11597b880b9eb28e) by Philipp Krüger).
- Ignore return code of spawned shells ([4f9a52b](https://github.com/Bubichoo-Teitichoo/pygwt/commit/4f9a52b0787049f5fafd1b9438389c5504589791) by Philipp Krüger).
- Hash branch name to get unique worktree name ([223f4bc](https://github.com/Bubichoo-Teitichoo/pygwt/commit/223f4bc748a064f100d419d0177e3f0cd5f31015) by Philipp Krüger).
- Handle error if one of the clone commands fail ([3c37682](https://github.com/Bubichoo-Teitichoo/pygwt/commit/3c3768245f92307718b7bac5c71d8601cc5ff6b1) by Philipp Krüger).
- Check if destination exists when cloning ([9af1def](https://github.com/Bubichoo-Teitichoo/pygwt/commit/9af1defa421785540c94793ca801e29dd6c18438) by Philipp Krüger).

### Code Refactoring

- Use git CLI to list worktrees ([8832309](https://github.com/Bubichoo-Teitichoo/pygwt/commit/883230915939924d62176f86f5f005d8d696a135) by Philipp Krüger).
- Use git API to clone repositories ([dce29ac](https://github.com/Bubichoo-Teitichoo/pygwt/commit/dce29acf7be9647d2c0141a92de5a1c763d4ce85) by Philipp Krüger).
- Use git API to install alias ([f1fe743](https://github.com/Bubichoo-Teitichoo/pygwt/commit/f1fe7433558e0fc45d657b342b917f6156d5017b) by Philipp Krüger).
- Remove excessive part from alias ([511c285](https://github.com/Bubichoo-Teitichoo/pygwt/commit/511c2857b8122aeef12f92177f20a70c846e02fb) by Philipp Krüger).
- Use Git API for 'add' command ([55d3a2a](https://github.com/Bubichoo-Teitichoo/pygwt/commit/55d3a2a154836813717f4ee39bbb19e7f98ffc0a) by Philipp Krüger).
- Move creation of worktree under Repository class ([f12831c](https://github.com/Bubichoo-Teitichoo/pygwt/commit/f12831c5ee40c5262d68e745a6103ef9aa5a78c4) by Philipp Krüger).
- Use open_worktree to detect prunable worktrees ([2d5fe83](https://github.com/Bubichoo-Teitichoo/pygwt/commit/2d5fe83cc1c0754b6b57969227c469ce8c0e9183) by Philipp Krüger).
- Move pygit abstraction layer into separate module ([cb5cd98](https://github.com/Bubichoo-Teitichoo/pygwt/commit/cb5cd98265cd4685ac68f1a23e1c9d9ac6d05067) by Philipp Krüger).
- Move code for root dir detection under Repository class ([a871bfe](https://github.com/Bubichoo-Teitichoo/pygwt/commit/a871bfe5539df13502fa08c515d72287b3a3b61a) by Philipp Krüger).
- Move Shell spwan code under Shell class ([aba6f4d](https://github.com/Bubichoo-Teitichoo/pygwt/commit/aba6f4d23340e8ec4d4b969b9396cb3fbc19da37) by Philipp Krüger).
- Handle all cases with create_branch_ex ([d30d2a1](https://github.com/Bubichoo-Teitichoo/pygwt/commit/d30d2a13b0f0a864d09f65548efa2030463a316d) by Philipp Krüger).
- Move typevar definition above function that uses it ([3ad00d2](https://github.com/Bubichoo-Teitichoo/pygwt/commit/3ad00d2a4513e975e44b8b7ff23e20bcb852724c) by Philipp Krüger).
- Use bitmaks to configure pushd ([6e850ce](https://github.com/Bubichoo-Teitichoo/pygwt/commit/6e850ce9d0e64a74a1d05979ae7a57ed48721e91) by Philipp Krüger).

