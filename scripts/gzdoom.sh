#!/bin/bash

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

category="max"
demo=""
difficulty="4"
files=""
iwad="doom2"
map="01"
pistolStart="$GZDOOM_DIR/pistolstart.pk3"
smoothDoom="$GZDOOM_DIR/SmoothDoom.pk3"
target=""
verbose=false

POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    opt="$1"
    param="$2"
    shifts=true

    case "$opt" in
        -c) check "-c" "$param"
            category="$param"
            ;;
        -d) check "-d" "$param"
            demo="$param"
            ;;
        -m) check "-m" "$param"
            map="$param"
            ;;
        -s) check "-s" "$param"
            difficulty="$param"
            ;;
        -t) check "-t" "$param"
            testFolder="_test/$param/"
            ;;
        v)  verbose=true
            ;;
        -*) error "No such option: $1"
            ;;
        *)  POSITIONAL_ARGS+=("$opt")
            shifts=false;;
    esac

    shift
    if [ "$shifts" = true ]; then
        shift
    fi
done
set -- "${POSITIONAL_ARGS[@]}"

if [ -z "$1" ]; then
    error "Need target."
fi
target="${1,,}"

targetFolder="$testFolder$target"
wadDir="$GZDOOM_DIR/wad/$targetFolder"
if [ ! -d "$wadDir" ]; then
    error "Could not find WAD dir: \"$wadDir\""
fi

files=()
for file in "$wadDir"/*; do
    if [ -f "$file" ]; then
        if [ "$(basename "$file" .bat)" = "$(basename "$file")" ] && \
           [ "$(basename "$file" .txt)" = "$(basename "$file")" ] && \
           [ "$(basename "$file" .rar)" = "$(basename "$file")" ] && \
           [ "$(basename "$file" .zip)" = "$(basename "$file")" ]; then

            files+=("$file")
        fi
    fi
done

case "$target" in
    "MM")
        pistolStart=""
        smoothDoom=""
        ;;
    "tntr")
        iwad="TNT"
        ;;
    "valiant")
        pistolStart=""
        smoothDoom=""
        ;;
esac

complevel=2
case "$iwad" in
    "TNT")  complevel=4
            ;;
    "Plutonia")
            complevel=4
            ;;
esac

for file in $smoothDoom $pistolStart; do
    if [ -n "$file" ]; then
        files+=("$file")
    fi
done

if [ "${#map}" = 1 ]; then
    map="0$map"
fi

outputDir="$GZDOOM_DIR/demo/$targetFolder/map$map"
demoPath="$outputDir/$DOOM_PLAYER-$target-$map-skill${difficulty}-${category}"

if [ -n "$demo" ]; then
    demoCommand="-playdemo"
    demoFile="${demoPath}_$demo.lmp"
else
    mkdir -p "$outputDir"
    demoCommand="-record"
    demoFile="${demoPath}_$(find "$outputDir" -maxdepth 1 -type f | wc -l).lmp"
fi

if [ "$verbose" = true ]; then
    set -x
fi

"$GZDOOM_DIR/gzdoom.exe" -file ${files[*]} \
                         -iwad "$iwad.wad" \
                         -complevel "$complevel" \
                         -skill "$difficulty" \
                         -warp "$map" \
                         "$demoCommand" "${demoFile[*]}" &
