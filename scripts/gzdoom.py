import argparse
import json
import os
import subprocess
import sys


IWADS = [ "doom", "doom2", "tnt", "plutonia" ]

MOD_FILES_IGNORE = [ ".bat", ".md", ".rar", ".gz", ".txt", ".zip" ]

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


def getDemoFile(executable, version, player, target, map, difficulty, category, demoNumber):
    directory = os.path.join(env("DOOM_DEMO_DIR"), executable, version, player, target, map)
    file = "-".join([player, target, map, difficulty, category])
    path = os.path.join(directory, file)

    doRecord = demoNumber is None or demoNumber == "" or int(demoNumber) < 0
    fullPath = (f"{path}_{demoNumber}" if doRecord else nextFile(path)) + ".lmp"

    fileExists = os.path.exists(fullPath)
    if fileExists:
        if doRecord:
            raise ValueError(f"File {fullPath} exists; name calculation broke.")
    elif not doRecord:
        raise ValueError(f"File {fullPath} doesn't exist.")

    return fullPath


def getIWad(configuration, targetWad):
    if targetWad in IWADS:
        return targetWad

    iwadKey = "iwad"
    if targetWad in configuration and iwadKey in configuration[targetWad]:
        return configuration[targetWad][iwadKey]

    return "doom2"


def getPWad(target, iwad, mapper):
    targetDir = "pwad"
    if target in IWADS:
        targetDir = "iwad"
    elif mapper:
        lowerMapper = mapper.lower()
        if lowerMapper in SPECIAL_MAPPERS:
            targetDir = SPECIAL_MAPPERS[lowerMapper]

    return verifyFile(os.path.join(f"{env('DOOM_DIR')}", f"{targetDir}", f"{target}", f"{target}.wad"))


def nextFile(filePath):
    number = 0
    result = f"{filePath}_{stringNumber(number, 3)}"

    while os.path.exists(result):
        number += 1
        result = f"{filePath}_{stringNumber(number, 3)}"

    return result

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


def readJson(filePath):
    with open(filePath) as contents:
        return json.load(contents)


def readMods(configuration, sourceDir, targetWad):
    modKey = "mods"

    if targetWad not in configuration or modKey not in configuration[targetWad]:
        return []

    result = []
    for file in configuration[targetWad][modKey]:
        fullPath = os.path.join(sourceDir, file)
        print(fullPath)

        if not os.path.isfile(fullPath) or os.path.splitext(file) in MOD_FILES_IGNORE:
            continue
        result.append(fullPath)

    return result


def stringNumber(number, amount):
    result = str(number)
    while len(result) < amount:
        result = f"0{result}"
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
    _addon             = []
    _category          = ""
    _command           = ""
    _compatibility     = ""
    _configuration     = {}
    _configurationPath = ""
    _demo              = ""
    _demoPath          = ""
    _difficulty        = SKILLS["uv"]
    _doLaunch          = True
    _executable        = env("GZDOOM_EXE")
    _files             = []
    _iwad              = "doom2"
    _iwadPath          = ""
    _map               = ""
    _mapper            = ""
    _modDir            = ""
    _mods              = ""
    _player            = env("DOOM_PLAYER")
    _skill             = ""
    _target            = ""
    _targetPath        = ""
    _warp              = ""
    _useMods           = True
    _verbose           = False
    _version           = env("GZDOOM_LATEST_VERSION")

    def __init__(self,
                 category,
                 compatibility,
                 demo,
                 configuration,
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

        addonPath         = os.path.join(os.path.dirname(self._executable), "addon")
        executablePath    = str(executable)
        modPath           = os.path.join(os.path.dirname(self._executable), "mod")
        skill, difficulty = SKILLS[str(skill)]
        targetPath        = getPWad(target, self._iwad, mapper)

        self._addon             = verifyDir(addonPath)
        self._configurationPath = verifyFile(configuration)
        self._executablePath    = verifyFile(executablePath)
        self._modDir            = verifyDir(modPath)
        self._targetPath        = verifyFile(targetPath)

        self._category                = str(category).lower()
        self._compatibility           = str(compatibility).lower()
        self._difficulty              = str(difficulty).lower()
        self._demo                    = str(demo)
        self._doLaunch                = bool(doLaunch)
        self._files                   = list(files)
        self._mapper                  = str(mapper).title()
        self._player                  = str(player).title()
        self._skill                   = str(skill).lower()
        self._target                  = str(target).lower()
        self._version                 = str(version).lower()
        self._useMods                 = bool(useMods)
        self._verbose                 = bool(verbose)

        self._command                 = "-record" if not self._demo else "-playdemo"
        self._configuration           = readJson(self._configurationPath)
        self._executable              = os.path.basename(self._executablePath).split(".")[0]
        self._iwad                    = getIWad(self._configuration, target)
        self._iwadPath                = verifyFile(os.path.join(env("DOOM_IWAD_DIR"), self._iwad, f"{self._iwad}.wad"))
        self._map, self._warp         = parseMap(map, self._iwad)
        self._mods                    = readMods(configuration, self._modDir, self._target) + autoLoad(self._addon)

        self._demoPath                = getDemoFile(self._executable,
                                                    self._version,
                                                    self._player,
                                                    self._target,
                                                    self._map,
                                                    self._difficulty,
                                                    self._category,
                                                    self._demo)


    def execute(self):
        if self._verbose:
            print(self)

        result = []
        result.append(self.executablePath())
        result.extend(["-compatmode", self.compatibility()])
        result.extend(["-iwad", self.iwadPath()])
        result.extend(["-file"] + self.files())
        result.extend(["-skill", self.skill()])
        result.extend(["-warp"] + self.warp())
        result.extend([self.demoCommand(), self.demoPath()])

        if self._doLaunch:
            return subprocess.call(result)
        else:
            print(" ".join(result))

    def __str__(self):
        commandString = self.demoCommand()
        commandString = commandString + ("" if len(commandString) == 9 else "  ")

        lines = ["Launch commands:"]
        lines.append(f"    executable: {self.executablePath()}")
        lines.append(f"        -compatmode: {self.compatibility()}")
        lines.append(f"        -file:       {self.files()}")
        lines.append(f"        -iwad:       {self.iwadPath()}")
        lines.append(f"        -skill:      {self.skill()}")
        lines.append(f"        -warp:       {self.warp()}")
        lines.append(f"        {self.demoCommand()}      {self.demoPath()}")

        return "\n".join(lines)

    def demoCommand(self):
        return self._command

    def demoPath(self):
        return self._demoPath

    def executable(self):
        return self._executable

    def executablePath(self):
        return self._executablePath

    def compatibility(self):
        return self._compatibility

    def difficulty(self):
        return self._difficulty

    def files(self):
        return [ self._targetPath ] + self._files + self._mods

    def iwad(self):
        return self._iwad

    def iwadPath(self):
        return self._iwadPath

    def target(self):
        return self._target

    def skill(self):
        return self._skill

    def warp(self):
        return [str(number) for number in self._warp]


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
                                                    default = False,
                                                    help    = "Print list of doom parameters.")

    parser.add_argument("-x", "--noLaunch",         action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Don't run the command.")

    result = parser.parse_args(argv)

    return Launch(
        category      = result.category,
        compatibility = result.compatibility,
        configuration = result.configuration,
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
    sys.exit(readLaunch(sys.argv[1:]).execute())
