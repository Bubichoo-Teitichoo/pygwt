#compdef git-twig

_git-twig() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[git-twig] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _GIT_TWIG_COMPLETE=zsh_complete git-twig)}")

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
    _git-twig "$@"
else
     # eval/source/. command, register function for later
    compdef _git-twig git-twig
fi

_git_twig_uninit() {
    if [ "$(whence -w git)" = "git: function" ]; then
        unset -f git
    fi
    if [ "$(whence -w git-twig)" = "git-twig: function" ]; then
        unset -f git-twig
    fi
}

_git_twig_uninit

export _GIT_TWIG_PATH=$(which git-twig)
export _GIT_PATH=$(which git)

git-twig () {
    if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
        dest=$($_GIT_TWIG_PATH $@)
        if [ $? -eq 0 ]; then
            echo "Switching to $dest"
            cd $dest
        fi
    else
        $_GIT_TWIG_PATH $@
    fi
}

git() {
    if [ "$1" = "twig" ]; then
        shift 1
        git-twig $@
    else
        $_GIT_PATH $@
    fi
}
