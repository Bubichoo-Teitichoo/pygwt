#compdef pygwt

_pygwt() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[pygwt] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _PYGWT_COMPLETE=zsh_complete pygwt)}")

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

_git-wt(){
    _pygwt
}

if [[ $zsh_eval_context[-1] == loadautofunc ]]; then
    # autoload from fpath, call function directly
    _pygwt "$@"
else
    # eval/source/. command, register function for later
    compdef _pygwt git-wt
    compdef _pygwt pygwt
fi

_pygwt_uninit() {
    if [ "$(whence -w pygwt)" = "pygwt: function" ]; then
        unset -f pygwt
    fi

    if [ "$(whence -w git)" = "git: function" ]; then
        unset -f git
    fi

    if [ "$(whence -w git-wt)" = "git-wt: function" ]; then
        unset -f git-wt
    fi
}

_pygwt_uninit

export _PYGWT_PATH=$(which pygwt)
export _GIT_PATH=$(which git)

pygwt () {
    if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
        cd $($_PYGWT_PATH $@)
    else
        $_PYGWT_PATH $@
    fi
}

git-wt () {
    if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
        cd $($_PYGWT_PATH $@)
    else
        $_PYGWT_PATH $@
    fi
}

git () {
    if [ "$1" = "wt" ]; then
        shift 1
        if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
            cd $($_PYGWT_PATH $@)
        else
            $_PYGWT_PATH $@
        fi
    else
        $_GIT_PATH $@
    fi
}
