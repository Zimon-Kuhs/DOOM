#!/bin/bash
#
# shellcheck disable=SC2806

here="$(readlink -f "$(dirname "$0")")"
name="$(basename "$(readlink -f "${0%.*}")")"
. "$here/common.sh"

demoMapString() {
    if [ -z "$1" ]; then
        exit 6
    fi

    mapIwad="doom2"
    if [ -n "$2" ]; then
        mapIwad="$2"
    fi

    result=""
    if [ "$mapIwad" = "doom" ]; then
        result="e${1:0:1}m${1:1:1}"
    else
        result="map$1"
    fi

    echo "$result"
}

episodicMap () {
    if [ -z "$1" ]; then
        exit 5
    fi

    length="${#1}"
    number="$1"

    case "$length" in
        2)  number="e${1:0:1}m${1:1:1}"
            ;;
        3)  number="e$1"
            ;;
        4)  ;;
        *)  error "Invalid map string $1."
            exit 6
            ;;
    esac

    episode="${number:1:1}"
    map="${number:3:1}"

    if (( episode < 1 )) || \
       (( episode > 5 )) || \
       (( map < 1 )) || \
       (( map > 9 )); then

       error "Invalid map numbers in $1 (e${episode}m${map})"
       exit 6
    fi

    echo "$number"
}

lowerCase() {
    echo "$1" | tr '[:upper:]' '[:lower:]'
}

say () {
    log "$name" "$1"
}

printSettings () {
    echo "Launch commands:"
    echo "    executable: $GZDOOM_DIR/$GZDOOM_LATEST_VERSION/gzdoom.exe"
    echo "        -compatmode: $1"
    echo "        -file:       $2"
    echo "        -iwad:       $3"
    echo "        -skill:      $4"
    echo "        -warp:       $5"
    echo "    $6 $7"
}

#~#~################################################################################################################~#~#
#   Default values.
#~#~################################################################################################################~#~#

category="max"
compatmode=2
demo=""
demoVersion="$GZDOOM_LATEST_VERSION"
files=""
iwad="doom2"
map=""
noLaunch=false
noModFiles=false
skill="4"
tester=""
verbose=false

modFiles=()
modFiles+=("smoothdoom.pk3")

#~#~################################################################################################################~#~#
#   Git Bash friendly getopt.
#~#~################################################################################################################~#~#

POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    opt="$1"
    param="$2"
    shifts=true

    case "$opt" in
        -a) demoVersion="$(checkArg "$opt" "$param")"
            ;;
        -c) category="$(checkArg "$opt" "$param")"
            ;;
        -d) demo="$(checkArg "$opt" "$param")"
            ;;
        -l) compatmode="$(checkArg "$opt" "$param")"
            ;;
        -m) if [ -n "$3" ] && [ "${3:0:1}" != "-" ]; then
                param="$2 $3"
                shift
            fi
            map="$(checkArg "$opt" "$param")"
            ;;
        -s) difficulty="$(checkArg "$opt" "$param")"
            ;;
        -t) tester="$(checkArg "$opt" "$param")"
            ;;
        -x) noLaunch=true
            shifts=false
            ;;
        -u) noModFiles=true
            shifts=false
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

if [ -z "$1" ]; then
    error "Need target wad."
    exit 1
fi

#~#~################################################################################################################~#~#
#   Fix/align args.
#~#~################################################################################################################~#~#

case "${#map}" in
    0)  ;;
    1)  map="0$map"
        ;;
    2)  ;;
    *)  map="${map:-2}"
        ;;
esac

targetWad="$(lowerCase "$1")"
tester="$(lowerCase "$tester")"

#~#~################################################################################################################~#~#
#   Figure out the WAD dir and check if it exists.
#~#~################################################################################################################~#~#

testDir=""
wadType="pwad"
if [ -n "$tester" ]; then
    testDir="$tester/"
    wadType="twad"
else
    for name in "doom" "doom2" "plutonia" "tnt"; do
        if [ "$name" = "$1" ]; then
            iwad="$1"
            wadType="iwad"
            break
        fi
    done
fi

if [ -z "$map" ]; then
    if [ "$iwad" = "doom" ]; then
        map="1 1"
    else
        map="01"
    fi
fi

#~#~################################################################################################################~#~#
#   Any PWAD-specific considerations should be added here.
#~#~################################################################################################################~#~#

case "$1" in
    "cchest")
        modFiles+=("midtwid2.wad")
        ;;
    "doom")
        modFiles+=("ultimidi.wad")
        ;;
    "doom2")
        modFiles+=("midtwid2.wad")
        ;;
    "plutonia")
        modFiles+=("plutmidi.wad")
        modFiles+=("plutmidi-np.wad")
        ;;
    "plutonia2")
        iwad="plutonia"
        ;;
    "sstruggle")
        iwad="doom"
        ;;
    "stickney")
        iwad="doom"
        ;;
    "tnt")
        modFiles+=("tntmidi.wad")
        modFiles+=("tntmidi-np.wad")
        ;;
    "tntr")
        iwad="tnt"
        ;;
    "valiant")
        modFiles=()
        ;;
esac

if [ "$noModFiles" = true ]; then
    modFiles=()
fi

dirSuffix="$testDir$targetWad"
iwadFile="$DOOM_IWAD_DIR/$iwad/$iwad.wad"
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

    if [ "$fullPath" = "$iwadFile" ] && [ "$wadType" = "iwad" ]; then
        continue
    fi

    if [ "$(isExtension $fullPath ".bat" ".rar" ".txt" ".zip")" = false ]; then
        files+=("$fullPath")
    fi
done

#~#~################################################################################################################~#~#
#   Check if mod files exist.
#~#~################################################################################################################~#~#

for file in "${modFiles[@]}"; do
    if [ -z "$file" ]; then
        continue
    fi

    modFile="$GZDOOM_DIR/$GZDOOM_LATEST_VERSION/mod/$file"
    if [ -f "$modFile" ]; then
        files+=("$modFile")
    else
        warning "Mod $modFile not found."
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
    4)  difficulty="uv"     ;;
    5)  difficulty="nm"     ;;
esac

mapDir="$(demoMapString "$map" "$iwad")"
demoDir="$DOOM_DEMO_DIR/gzdoom/$demoVersion/$dirSuffix/$mapDir"
demoName="$DOOM_PLAYER-$1-$mapDir-$difficulty-${category}"

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

filesString="${files[*]}"
if [ "$verbose" = true ]; then
    printSettings "$compatmode" \
                  "$filesString" \
                  "$iwadFile" \
                  "$skill" \
                  "$map" \
                  "$demoCommand" \
                  "${demoFile[*]}"
fi

if [ "$noLaunch" = true ]; then
    exit 0
fi

"$GZDOOM_DIR/$GZDOOM_LATEST_VERSION/gzdoom.exe" -compatmode "$compatmode" \
                         -file "${files[@]}" \
                         -iwad "$iwadFile" \
                         -skill "$skill" \
                         -warp $map \
                         "$demoCommand" "${demoFile[*]}" &
