#!/bin/bash

here="$(readlink -f "$(dirname "$0")")"
name="$(basename "$(readlink -f "${0%.*}")")"
. "$here/common.sh"

episodicMap () {
    if [ -z "$1" ]; then
        exit 5
    fi

    length="${#1}"
    number="$1"

    case "$length" in
        2)  number="e${1:0:1}m${1:1:1}"
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

say () {
    log "$name" "$1"
}

printSettings () {
    echo "Launch commands:"
    echo "    executable: $GZDOOM_DIR/gzdoom.exe"
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
map="01"
noLaunch=false
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
        -a) demoVersion="$(checkArg "$opt" "$param")"
            ;;
        -c) category="$(checkArg "$opt" "$param")"
            ;;
        -d) demo="$(checkArg "$opt" "$param")"
            ;;
        -l) compatmode="$(checkArg "$opt" "$param")"
            ;;
        -m) map="$(checkArg "$opt" "$param")"
            ;;
        -s) difficulty="$(checkArg "$opt" "$param")"
            ;;
        -t) tester="$(checkArg "$opt" "$param")"
            ;;
        -x) noLaunch=true
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

#~#~################################################################################################################~#~#
#   Any PWAD-specific considerations should be added here.
#~#~################################################################################################################~#~#

case "$1" in
    "doom")
        map="$(episodicMap "$map")" || exit 6
        ;;
    "plutonia")
        ;;
    "plutonia2")
        iwad="plutonia"
        ;;
    "tnt")
        modFiles+=("TNTmidi.wad")
        modFiles+=("TNTmidi-np.wad")
        ;;
    "tntr")
        iwad="tnt"
        ;;
    "valiant")
        modFiles=()
        ;;
esac
iwadFile="$DOOM_IWAD_DIR/$iwad/$iwad.wad"

dirSuffix="$testDir$targetWad"
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

demoDir="$DOOM_DEMO_DIR/gzdoom/$demoVersion/$dirSuffix/map$map"
demoName="$DOOM_PLAYER-$1$map-$difficulty-${category}"

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

"$GZDOOM_DIR/gzdoom.exe" -compatmode "$compatmode" \
                         -file "${files[@]}" \
                         -iwad "$iwadFile" \
                         -skill "$skill" \
                         -warp "$map" \
                         "$demoCommand" "${demoFile[*]}" &
