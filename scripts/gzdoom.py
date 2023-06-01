import argparse
import json
import os
import subprocess
import sys


IWADS = [ "doom", "doom2", "tnt", "plutonia" ]

MOD_FILES_IGNORE = [ ".bat", ".md", ".rar", ".gz", ".txt", ".zip" ]

PWADS = None

SPECIAL_MAPPERS = {
    "cinnamon": "zwad",
    "garlic":   "bwad"
}

SKILLS = {
    "itytd": (1, "itytd"),  "1": (1, "itytd"),
    "hntr":  (2, "hntr"),   "2": (2, "hntr"),
    "hmp":   (3, "hmp"),    "3": (3, "hmp"),
    "uv":    (4, "uv"),     "4": (4, "uv"),
    "nm":    (5, "nm"),     "5": (5, "nm")
}


def autoLoad(modDir):
    result = []
    for file in [ fileName for fileName in os.listdir(modDir) ]:
        fullPath = os.path.join(modDir, file)

        if not os.path.isfile(fullPath) or os.path.splitext(file) in MOD_FILES_IGNORE:
            continue
        result.append(fullPath)

    return result


def env(parameter):
    result = os.environ.get(parameter.split("$")[-1])
    if result is None:
        raise ValueError(f"No such environment variable: {result}.")
    return result


def getIWad(targetWad):
    if targetWad in IWADS:
        return targetWad

    iwadKey = "iwad"
    if targetWad in PWADS and iwadKey in PWADS[targetWad]:
        return PWADS[targetWad][iwadKey]

    return "doom2"


def getPWad(target, iwad, mapper):
    targetDir = "pwad"
    if target == iwad:
        targetDir = "iwad"
    elif mapper:
        lowerMapper = mapper.lower()
        if lowerMapper in SPECIAL_MAPPERS:
            targetDir = SPECIAL_MAPPERS[lowerMapper]

    return verifyFile(os.path.join(f"{env('DOOM_DIR')}", f"{targetDir}", f"{target}", f"{target}.wad"))


def parseMap(mapList, iwad):
    amount = len(mapList)
    if amount <= 0 or amount > 2:
        raise ValueError(f"Invalid map numbers: {mapList}")

    if amount == 1 and iwad == "doom" or amount == 2 and iwad != "doom":
        raise ValueError(f"Map number {mapList} is invalid for IWAD {iwad}.")

    numbers = [ int(number) for number in mapList ]
    if amount == 2:
        return f"e{mapList[0]}m{mapList[1]}", numbers

    return "map" + ("0" if numbers[0] < 10 else "") + str(numbers[0]), numbers


def readMods(sourceDir, targetWad):
    global PWADS
    modKey = "mods"

    if targetWad not in PWADS or modKey not in PWADS[targetWad]:
        return []

    result = []
    for file in PWADS[targetWad][modKey]:
        fullPath = os.path.join(sourceDir, file)
        print(fullPath)

        if not os.path.isfile(fullPath) or os.path.splitext(file) in MOD_FILES_IGNORE:
            continue
        result.append(fullPath)

    return result


def verifyDir(filePath):
    if not os.path.exists(filePath):
        raise ValueError(f"No such file: {filePath}.")
    if not os.path.isdir(filePath):
        raise ValueError(f"Not a directory: {filePath}.")
    return filePath


def verifyFile(filePath):
    if not os.path.exists(filePath):
        raise ValueError(f"No such file: {filePath}.")
    if not os.path.isfile(filePath):
        raise ValueError(f"Not a file: {filePath}.")
    return filePath


class Launch:
    _addon         = []
    _category      = ""
    _command       = ""
    _compatibility = ""
    _demo          = ""
    _difficulty    = SKILLS["uv"]
    _doLaunch      = True
    _executable    = env("GZDOOM_EXE")
    _files         = []
    _iwad          = "doom2"
    _map           = ""
    _mapper        = ""
    _modDir        = ""
    _mods          = ""
    _player        = env("DOOM_PLAYER")
    _skill         = ""
    _target        = ""
    _targetPath    = ""
    _warp          = ""
    _useMods       = True
    _verbose       = False
    _version       = env("GZDOOM_LATEST_VERSION")

    def __init__(self,
                 category,
                 compatibility,
                 demo,
                 doLaunch,
                 executable,
                 files,
                 map,
                 mapper,
                 player,
                 skill,
                 target,
                 useMods,
                 verbose,
                 version):

        iwad = getIWad(target)

        addonPath      = os.path.join(os.path.dirname(self._executable), "addon")
        executablePath = str(executable)
        iwadPath       = os.path.join(env("DOOM_IWAD_DIR"), iwad, f"{iwad}.wad")
        modPath        = os.path.join(os.path.dirname(self._executable), "mod")
        targetPath     = getPWad(target, self._iwad, mapper)

        self._addon      = verifyDir(addonPath)
        self._iwad       = verifyFile(iwadPath)
        self._executable = verifyFile(executablePath)
        self._modDir     = verifyDir(modPath)
        self._targetPath = verifyFile(targetPath)

        self._category                = str(category)
        self._compatibility           = str(compatibility)
        self._doLaunch                = bool(doLaunch)
        self._files                   = list(files)
        self._mapper                  = str(mapper)
        self._player                  = str(player)
        self._target                  = str(target)
        self._version                 = str(version)
        self._useMods                 = bool(useMods)
        self._verbose                 = bool(verbose)

        self._command = "-record" if not self._demo else "-playdemo"
        self._demo                    = 0 if not demo else int(demo)
        self._skill, self._difficulty = SKILLS[str(skill)]

        self._map, self._warp         = parseMap(map, self._iwad)
        self._mods                    = readMods(self._modDir, self._target) + autoLoad(self._addon)


    def execute(self):
        if self._verbose:
            print(self)

        result = []
        result.append(self.executable())
        result.extend(["-compatmode", self.compatibility()])
        result.extend(["-iwad", self.iwad()])
        result.extend(["-file"] + self.files())
        result.extend(["-warp"] + [str(part) for part in self.warp()])
        result.extend([self.demoCommand(), self.demoPath()])

        return result

    def executable(self):
        return self._executable

    def compatibility(self):
        return self._compatibility

    def difficulty(self):
        return self._difficulty

    def files(self):
        return [ self._targetPath ] + self._files + self._mods

    def iwad(self):
        return self._iwad

    def target(self):
        return self._target

    def skill(self):
        return self._skill

    def warp(self):
        return [str(number) for number in self._warp]

    def demoCommand(self):
        return self._command

    def demoFile(self):
        return "-".join([
            self._player,
            self._target,
            self._map,
            self._difficulty,
            self._category,
        ]) + ".lmp"

    def demoDir(self):
        return os.path.join(env("DOOM_DEMO_DIR"),
                            self._player.lower(),
                            "gzdoom",
                            self._version,
                            self._target,
                            self._map)

    def demoPath(self):
        return os.path.join(self.demoDir(), self.demoFile())


    def __str__(self):
        commandString = self.demoCommand()
        commandString = commandString + ("" if len(commandString) == 9 else "  ")

        lines = ["Launch commands:"]
        lines.append(f"    executable: {self.executable()}")
        lines.append(f"        -compatmode: {self.compatibility()}")
        lines.append(f"        -file:       {self.files()}")
        lines.append(f"        -iwad:       {self.iwad()}")
        lines.append(f"        -skill:      {self.skill()}")
        lines.append(f"        -warp:       {self.warp()}")
        lines.append(f"        {self.demoCommand()}      {self.demoPath()}")
        return "\n".join(lines)

def readLaunch(argv):
    parser = argparse.ArgumentParser(prog = "DOOM Launcher", description = "DOOM Launcher Helper")
    parser.add_argument("target")

    parser.add_argument("-c", "--category",         default = "max",
                                                    help    = "Type of map completion type.")

    parser.add_argument("-d", "--demo",             default = "",
                                                    help    = "Run demo; argument is demo number.",
                                                    nargs   = "?")

    parser.add_argument("-e", "--executable",       default = env("GZDOOM_EXE"),
                                                    help    = "Executable to use.")

    parser.add_argument("-f", "--files",            default = [],
                                                    help    = "Extra files; use for testing.",
                                                    nargs   = "*")

    parser.add_argument("-g", "--configuration",    default = os.path.join(os.path.dirname(sys.argv[0]), "pwads.json"),
                                                    help    = "Configuration file to use.")

    parser.add_argument("-m", "--map",              default = "1",
                                                    help    = "Map number.",
                                                    nargs   = "+")

    parser.add_argument("-o", "--compatibility",    default = "2",
                                                    help    = "Compatibility setting (compatmode).")

    parser.add_argument("-p", "--player",           help    = "Player name.",
                                                    default = env("DOOM_PLAYER"))

    parser.add_argument("-r", "--version",          default = env("GZDOOM_LATEST_VERSION"),
                                                    help    = "GZDoom version.")

    parser.add_argument("-s", "--skill",            help    = "Difficulty.",
                                                    default = "4")

    parser.add_argument("-t", "--mapper",           help    = "Mapper name.",
                                                    default = "")

    parser.add_argument("-u", "--unmodded",         default = "",
                                                    help    = "Don't load any mod files.")

    parser.add_argument("-v", "--verbose",          action  = "store_const",
                                                    const   = True,
                                                    help    = "Print list of doom parameters.")

    parser.add_argument("-x", "--noLaunch",         default = "False",
                                                    help    = "Don't run the command.")

    result = parser.parse_args(argv)

    with open(result.configuration) as contents:
        global PWADS
        PWADS = json.load(contents)

    return Launch(
        category      = result.category,
        compatibility = result.compatibility,
        demo          = result.demo,
        doLaunch      = not result.noLaunch,
        executable    = result.executable,
        files         = result.files,
        map           = result.map,
        player        = result.player,
        skill         = result.skill,
        target        = result.target,
        mapper        = result.mapper,
        useMods       = not result.unmodded,
        verbose       = result.verbose,
        version       = result.version,
    )


if __name__ == "__main__":
    command = readLaunch(sys.argv[1:]).execute()
    print(command)
    subprocess.call(command)
