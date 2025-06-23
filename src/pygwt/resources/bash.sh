_git_wt_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$((COMP_CWORD)) _GIT_WT_COMPLETE="bash_complete" $1)

    for completion in $response; do
        IFS=',' read type value <<< "$completion"

        if [[ $type == 'dir' ]]; then
            COMPREPLY=()
            compopt -o dirnames
        elif [[ $type == 'file' ]]; then
            COMPREPLY=()
            compopt -o default
        elif [[ $type == 'plain' ]]; then
            COMPREPLY+=($value)
        fi
    done

    return 0
}

_git_wt_alias_completion() {
    if [ "${COMP_WORDS[1]}" = "wt" ]; then
        COMP_WORDS=("git-wt" ${COMP_WORDS[@]:2})
        COMP_CWORD=$((COMP_CWORD-1))

        _git_wt_completion git-wt
        return 0
    fi

    return 1
}

_git_wt_completion_setup() {
    complete -o nosort -F _git_wt_completion git-wt
    complete -o nosort -F _git_wt_alias_completion git
}

_git_wt_uninit() {
    if [[ $(type -t git-wt) = function ]]; then
        unset -f git-wt
    fi

    if [[ $(type -t git) = function ]]; then
        unset -f git
    fi
}

_git_wt_completion_setup;
_git_wt_uninit;

export _GIT_WT_PATH=$(which git-wt)
export _GIT_PATH=$(which git)

git () {
    if [ "$1" = "wt" ]; then
        shift 1
        git-wt $@
    else
        $_GIT_PATH $@
    fi
}

git-wt () {
    if [ "$1" = "switch" ] || ([ "$1" = "repository" ] && [ "$2" = "switch" ]); then
        dest=$($_GIT_WT_PATH $@)
        if [ $? -eq 0 ]; then
            echo "Switching to $dest"
            cd $dest
        fi
    else
        $_GIT_WT_PATH $@
    fi
}
