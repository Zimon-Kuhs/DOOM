#!/bin/bash
#
# shellcheck disable=SC2005

log () {
    echo "[$1]: $2"
}

error () {
    echo "$(log "ERROR" "$1")" 1>&2
}

warning () {
    log "WARNING" "$1"
}

checkArg () {
    if [ -z "$1" ]; then
        error "Nothing to check."
    fi

    if [ -z "$2" ]; then
        error "$1 expects an argument."
    fi
    echo "$2"
}

isExtension() {
    file="$(basename "$1")"

    for extension in "${@:2}"; do
        if [[ $file == *$extension ]]; then
            echo true
        fi
    done
    echo false
}


