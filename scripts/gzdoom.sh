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

demo=""
difficulty="4"
files=""
iwad="doom2"
map="01"
mapper=""
pistolStart="$GZDOOM_DIR/pistolstart.pk3"
smoothDoom="$GZDOOM_DIR/SmoothDoom.pk3"
target=""

POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case "$1" in
        -d) check "-d" "$2"
            demo="$2"
            shift
            shift
            ;;
        -m) check "-m" "$2"
            map="$2"
            shift
            shift
            ;;
        -s) check "-s" "$2"
            difficulty="$2"
            shift
            shift
            ;;
        -t) check "-t" "$2"
            mapper="$2"
            testFolder="_test/$mapper/"
            shift
            shift
            ;;
        -*) error "No such option: $1"
            ;;
        *)  POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done
echo "$@"
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
echo "file $smoothDoom $pistolStart"
for file in $smoothDoom $pistolStart; do
    if [ -n "$file" ]; then
        files+=("$file")
    fi
done

if [ "${#map}" = 1 ]; then
    map="0$map"
fi

outputDir="$GZDOOM_DIR/demo/$targetFolder/map$map"
demoPath="$outputDir/$DOOM_PLAYER-$target-$map-skill${difficulty}"

if [ -n "$demo" ]; then
    demoCommand="-playdemo"
    demoFile="-playdemo ${demoPath}_$demo.lmp"
else
    mkdir -p "$outputDir"
    demoCommand="-record"
    demoFile="${demoPath}_$(find "$outputDir" -maxdepth 1 -type f | wc -l).lmp"
fi

set -x
"$GZDOOM_DIR/gzdoom.exe" -file ${files[*]} \
                         -iwad "$iwad.wad" \
                         -skill "$difficulty" \
                         -warp "$map" \
                         "$demoCommand" "${demoFile[*]}" &
