#!/bin/bash

say () {
    echo "[$(basename "$(dirname "${0%.*}"))]$1")"
}

error () {
    if [ -n "$1" ]; then
        echo "$1"
    fi

    code=1
    if [ -n "$2" ]; then
        code="$2"
    fi

    exit "$code"
}

check () {
    if [ -z "$1" ]; then
        error "Nothing to check."
    fi

    if [ -z "$2" ]; then
        error "$1 expects an argument."
    fi
}

isExtension() {
    file="(basename $1)"

    for extension in ${*:2}; do
        if [ "$(basename "$file" $extension)" = "$file" ]; then
            echo true
        fi
    done
    echo false
}

warning () {
    say "[WARNING]: $1"
}

#~#~################################################################################################################~#~#
#   Default values.
#~#~################################################################################################################~#~#

category="max"
demo=""
files=""
iwad="DOOM2"
map="01"
skill="4"
target=""
tester=""
verbose=false

modFiles=()
modFiles+=("SmoothDoom.pk3")

#~#~################################################################################################################~#~#
#   Git Bash friendly getopt.
#~#~################################################################################################################~#~#

POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    opt="$1"
    param="$2"
    shifts=true

    case "$opt" in
        -c) category="$(check "$opt" "$param")"
            ;;
        -d) demo="$(check "$opt" "$param")"
            ;;
        -m) map="$(check "$opt" "$param")"
            ;;
        -s) difficulty="$(check "$opt" "$param")"
            ;;
        -t) tester="$(check "$opt" "$param")"
            ;;
        v)  verbose=true
            shifts=false
            ;;
        -*) error "No such option: $1"
            ;;
        *)  POSITIONAL_ARGS+=("$opt")
            shifts=false
            ;;
    esac

    shift
    if [ "$shifts" = true ]; then
        shift
    fi
done
set -- "${POSITIONAL_ARGS[@]}"

#~#~################################################################################################################~#~#
#   Figure out the WAD dir and check if it exists.
#~#~################################################################################################################~#~#

if [ -z "$1" ]; then
    error "Need target."
fi

testDir=""
wadType="pwad"
if [ -n "$tester" ]; then
    testDir="$tester/"
    wadType="twad"
fi

dirSuffix="$testDir${1,,}"
wadDir="$wadType/$dirSuffix"
if [ ! -d "$wadDir" ]; then
    error "Could not find WAD dir: $wadDir"
fi

#~#~################################################################################################################~#~#
#   Add extra files for the '-file' parameter.
#~#~################################################################################################################~#~#

files=()
for file in "$wadDir"/*; do
    if [ -f "$file" ] && \
       [ "$(isExtension "$file" ".bat" ".rar" ".txt" ".zip")" = false ]; then
        files+=("$file")
    fi
done

#~#~################################################################################################################~#~#
#   Set IWAD and complevel.
#   Also, any PWAD-specific considerations should be added here.
#~#~################################################################################################################~#~#

case "$target" in
    "plutonia2")
        iwad="PLUTONIA"
        ;;
    "tntr")
        iwad="TNT"
        ;;
    "valiant")
        modFiles=()
        ;;
esac

complevel=2
case "$iwad" in
    "DOOM")     complevel=9 ;;
    "TNT")      complevel=4 ;;
    "Plutonia") complevel=4 ;;
esac

#~#~################################################################################################################~#~#
#   Check if mod files exist.
#~#~################################################################################################################~#~#

for file in "${modFiles[@]}"; do
    if [ -z "$file" ]; then
        continue
    fi

    modFile="$GZDOOM_MOD_DIR/$file"
    if [ -f "$modFile" ]; then
        files+=("$file")
    else
        warning "$modFile not found."
    fi
done

#~#~################################################################################################################~#~#
#   Calculate the name of the demo file.
#~#~################################################################################################################~#~#

if [ "${#map}" = 1 ]; then
    map="0$map"
fi

difficulty="uv"
case "$skill" in
    1)  difficulty="itytd"  ;;
    2)  difficulty="hntr"   ;;
    3)  difficulty="hmp"    ;;
    5)  difficulty="nm"     ;;
esac

demoDir="$DOOM_DEMO_DIR/$GZDOOM_LATEST_VERSION/$dirSuffix/map$map"
demoName="$DOOM_PLAYER-$target-$map-$difficulty-${category}"

if [ -n "$demo" ]; then
    demoCommand="-playdemo"
    demoNumber="$demo"
else
    demoCommand="-record"
    demoNumber="$(find "$demoDir" -maxdepth 2 -type f -name "*.lmp" | wc -l)"

    mkdir -p "$demoDir"
fi
demoFile="${demoName}_$demoNumber"

if [ -n "$demo" ]; then
    if [ ! -f "$demoFile" ]; then
        error "No such demo file exists: $demoFile"
    fi
elif [ -f "$demoFile" ]; then
    error "Critical error, $demoFile already exists somehow."
fi

if [ "$verbose" = true ]; then
    set -x
fi

"$GZDOOM_DIR/gzdoom.exe" -file "${files[@]}" \
                         -iwad "$iwad.wad" \
                         -complevel "$complevel" \
                         -skill "$difficulty" \
                         -warp "$map" \
                         "$demoCommand" "${demoFile[*]}" &
