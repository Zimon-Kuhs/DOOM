#!/bin/bash

findWad () {

locations=()
locations+=("$DOOM_BWAD_DIR")
locations+=("$DOOM_IWAD_DIR")
locations+=("$DOOM_PWAD_DIR")
locations+=("$DOOM_TWAD_DIR")
locations+=("$DOOM_ZWAD_DIR")

for wadDir in "${locations[@]}"; do
    if [ -d "$wadDir" ]; then
        for dir in $(listDir "$wadDir"); do
            if [ "$(basename "$dir")" = "$1" ]; then

                wadFile="$dir/$1.wad"
                if [ ! -f "$wadFile" ]; then
                    echo "Warning: $dir found but $wadFile not found."
                fi
                echo "$dir"
                exit 0
            fi
        done
    fi
done

}
