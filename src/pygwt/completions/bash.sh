_pygwt_completion() {
    local IFS=$'\n'
    local response

    response=$(env COMP_WORDS="${COMP_WORDS[*]}" COMP_CWORD=$((COMP_CWORD)) _PYGWT_COMPLETE="bash_complete" $1)

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

_pygwt_alias_completion() {
    if [ "${COMP_WORDS[1]}" = "wt" ]; then
        COMP_WORDS=("pygwt" ${COMP_WORDS[@]:2})
        COMP_CWORD=$((COMP_CWORD-1))

        _pygwt_completion pygwt
        return 0
    fi

    return 1
}

_pygwt_completion_setup() {
    complete -o nosort -F _pygwt_completion pygwt
    complete -o nosort -F _pygwt_alias_completion git
}

_pygwt_completion_setup;
