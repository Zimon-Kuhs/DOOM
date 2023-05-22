#!/bin/bash

here="$(readlink -f "$(dirname "$0")")"
name="$(basename "$(readlink -f "${0%.*}")")"
. "$here/common.sh"

say () {
    log "$name" "$1"
}

#~#~################################################################################################################~#~#
#   Default values.
#~#~################################################################################################################~#~#

category="max"
demo=""
demoVersion="$GZDOOM_LATEST_VERSION"
files=""
iwad="doom2"
map="01"
skill="4"
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
        -a) demoVersion="$(check "$opt" "$param")"
            ;;
        -m) map="$(check "$opt" "$param")"
            ;;
        -s) difficulty="$(check "$opt" "$param")"
            ;;
        -t) tester="$(check "$opt" "$param")"
            ;;
        -v) verbose=true
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
    error "Need target wad."
    exit 1
fi
targetWad="$1"

testDir=""
wadType="pwad"
if [ -n "$tester" ]; then
    testDir="$tester"
    wadType="twad"
fi

dirSuffix="$testDir/$targetWad"
wadDir="$DOOM_DIR/$wadType/$dirSuffix"
if [ ! -d "$wadDir" ]; then
    error "Could not find WAD dir: $wadDir"
    exit 2
fi

#~#~################################################################################################################~#~#
#   Add extra files for the '-file' parameter.
#~#~################################################################################################################~#~#

files=()
for file in "$wadDir"/*; do
    fullPath="$(readlink -f "$file")"

    if [ "$(isExtension $fullPath ".bat" ".rar" ".txt" ".zip")" = false ]; then
        files+=("$fullPath")
    fi
done

#~#~################################################################################################################~#~#
#   Set IWAD and complevel.
#   Also, any PWAD-specific considerations should be added here.
#~#~################################################################################################################~#~#

case "$1" in
    "plutonia2")
        iwad="plutonia"
        ;;
    "tntr")
        iwad="tnt"
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
        files+=("$modFile")
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

demoDir="$DOOM_DEMO_DIR/$demoVersion/$dirSuffix/map$map"
demoName="$DOOM_PLAYER-$1-$map-$difficulty-${category}"

mkdir -p "$demoDir"
if [ -n "$demo" ]; then
    demoCommand="-playdemo"
    demoNumber="$demo"
else
    demoCommand="-record"
    demoNumber="$(find "$demoDir" -maxdepth 2 -type f -name "*.lmp" | wc -l)"

fi
demoFile="$demoDir/${demoName}_$demoNumber.lmp"

if [ -n "$demo" ]; then
    if [ ! -f "$demoFile" ]; then
        error "No such demo file exists: $demoFile"
        exit 3
    fi
elif [ -f "$demoFile" ]; then
    error "Critical error, $demoFile already exists somehow."
    exit 4
fi

if [ "$verbose" = true ]; then
    set -x
fi

"$GZDOOM_DIR/gzdoom.exe" -file "${files[@]}" \
                         -iwad "$DOOM_IWAD_DIR/$iwad.wad" \
                         -complevel "$complevel" \
                         -skill "$skill" \
                         -warp "$map" \
                         "$demoCommand" "${demoFile[*]}" &
