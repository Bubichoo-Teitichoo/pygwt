#compdef git-wt

_git-wt() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[git-wt] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _GIT_WT_COMPLETE=zsh_complete git-wt)}")

    for type key descr in ${response}; do
        if [[ "$type" == "plain" ]]; then
            if [[ "$descr" == "_" ]]; then
                completions+=("$key")
            else
                completions_with_descriptions+=("$key":"$descr")
            fi
        elif [[ "$type" == "dir" ]]; then
            _path_files -/
        elif [[ "$type" == "file" ]]; then
            _path_files -f
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    # autoload from fpath, call function directly
    _git-wt "$@"
else
     # eval/source/. command, register function for later
    compdef _git-wt git-wt
fi

_git_wt_uninit() {
    if [ "$(whence -w git)" = "git: function" ]; then
        unset -f git
    fi

    if [ "$(whence -w git-wt)" = "git-wt: function" ]; then
        unset -f git-wt
    fi
}

_git_wt_uninit

export _GIT_WT_PATH=$(which git-wt)
export _GIT_PATH=$(which git)

git-wt () {
    if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
        cd $($_GIT_WT_PATH $@)
    else
        $_GIT_WT_PATH $@
    fi
}

git () {
    if [ "$1" = "wt" ]; then
        shift 1
        git-wt $@
    else
        $_GIT_PATH $@
    fi
}
