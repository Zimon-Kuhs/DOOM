import argparse
import os
import sys


def env(parameter):
    result = os.environ.get(parameter.split("$")[-1])
    if result is None:
        raise ValueError(f"No such environment variable: {result}.")
    return result


def isDoomMap(name):
    return len(name) == 4 and \
           name[0] == "e" and \
           name[2] == "m" and \
           name[1].isnumeric() and \
           name[3].isnumeric()


def isDoom2Map(name):
    return len(name) == 5 and name[0:3] == "map" and name[3:].isnumeric()


def countSequences(path, mapType):
    check = isDoomMap if mapType == "doom" else isDoom2Map

    sequences = []
    sequence = []

    dirList = os.listdir(path)
    dirList.sort()

    for file in dirList:
        number = getNumber(file)
        if len(sequence) == 0 or sequence[-1] == number - 1:
            sequence.append(number)
        else:
            sequences.append(sequence)
            sequence = []

    if len(sequence) > 0:
        sequences.append(sequence)

    return sum([ len(seqeunce) for seqeunce in sequences ])


def getNumber(name):
    return (int(name[1]) * 9 + int(name[3])) if isDoomMap(name) else int(name[3:])


def getMapType(dirPath):
    mapType = None
    for file in os.listdir(dirPath):
        fullPath = os.path.join(dirPath, file)
        if os.path.isdir(fullPath):

            if isDoom2Map(file):
                if mapType == "doom":
                    raise ValueError(f"Ambiguous directory {dirPath}.")
                else:
                    mapType = "doom2"

            elif isDoomMap(file):
                if mapType == "doom2":
                    raise ValueError(f"Ambiguous directory {dirPath}.")
                else:
                    mapType = "doom"

    if mapType is None:
        raise ValueError(f"Could not deduce map type for {dirPath}.")

    return mapType


if __name__ == "__main__":
    argv = sys.argv[1:]
    argc = len(argv)

    baseDir = os.path.join(env("DOOM_DEMO_DIR"), "gzdoom", env("GZDOOM_LATEST_VERSION"), env("DOOM_PLAYER"))
    targets = None
    if argc >= 1:
        targets = [argv[0]]
    else:
        targets = [target for target in os.listdir(baseDir) if target[0] != "."]

    width = max([len(target) for target in targets])

    for target in targets:
        fullPath = os.path.join(baseDir, target)
        if len(os.listdir()) == 0:
            continue

        mapType = getMapType(fullPath)

        maxAmount = 45 if target == "doom" else (36 if mapType == "doom" else 32)

        namePart = f"{target}:{(width - (len(target) + 1)) * ' '}"
        print(f"{namePart}{round(10000 * countSequences(fullPath, mapType) / maxAmount) / 100}%")
