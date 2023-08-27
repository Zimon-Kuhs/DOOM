import argparse
import datetime
import json
import os
import subprocess
import sys

ARG_TO_SETTING = {
    "--fast":       "fast",
    "--respawn":    "respawn",
    "--nomonsters": "nomo"
}

IWADS = [ "doom", "doom2", "tnt", "plutonia" ]

MOD_FILES_IGNORE = [ ".bat", ".md", ".rar", ".gz", ".txt", ".zip" ]

SPECIAL_MAPPERS = {
    "Cinnamon": "zwad",
    "Garlic":   "bwad"
}

SETTING_COMPATIBILITY = [
    { "-fast", "-respawn" },
    { "-nomo" }
]

SETTING_KEY = {
    "fast":    "f",
    "nomo":    "o",
    "respawn": "r"
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


def demoFileSetup(executable, version, player, mapper, target, map, difficulty, category, settings, demo):
    dirBase  = os.path.join(env("DOOM_DEMO_DIR"), executable, version, player)

    if mapper is not None and mapper != "":
        dirBase = os.path.join(dirBase, ".test", mapper)

    demoDir  = os.path.join(dirBase, target, map)
    demoFile = "-".join([player, target, map, difficulty])

    extraPart = ""
    for flag, setting in settings.items():
        if setting:
            extraPart = f"{extraPart}{SETTING_KEY[flag]}"

    attempts = -1
    result = ""
    fullPath = f"{os.path.join(demoDir, demoFile)}{extraPart}-{category}"
    if demo is None or demo < 0:
        result, attempts = nextFile(fullPath, ".lmp")

        if os.path.exists(result):
            raise ValueError(f"File for -record already exists. {result}")

        os.makedirs(demoDir, exist_ok = True)

    else:
        if not isinstance(demo, int):
            raise ValueError(f"Demo number should be integer: {demo} ({type(demo)}).")

        result = f"{fullPath}_{stringNumber(str(demo), 3)}.lmp"

        if not os.path.exists(result):
            raise ValueError(f"File for -playdemo doesn't exist. {result}")


    return f"{result}", attempts


def env(parameter):
    result = os.environ.get(parameter.split("$")[-1])
    if result is None:
        raise ValueError(f"No such environment variable: {result}.")
    return result


def getIWad(configuration, targetWad):
    if targetWad in IWADS:
        return targetWad

    iwadKey = "iwad"
    if targetWad in configuration and iwadKey in configuration[targetWad]:
        return configuration[targetWad][iwadKey]

    return "doom2"


def getPWad(target, mapper):
    isIwad = target in IWADS
    isSwad = mapper in SPECIAL_MAPPERS
    isTwad = mapper is not None and mapper != ""

    checks = [ isIwad, isSwad, isTwad ]

    if sum(checks) > 1:
        raise ValueError(f"Ambiguous WAD type; IWad: {isIwad}, SWad: {isSwad}, TWad: {isTwad}.")

    targetType = "pwad"
    if isIwad:
        targetType = "iwad"
    elif isSwad:
        targetType = SPECIAL_MAPPERS[mapper]
    elif isTwad:
        targetType = "twad"

    targetDir = f"{targetType}"
    if isTwad or isSwad:
        targetDir = os.path.join(targetDir, mapper)

    return verifyFile(os.path.join(f"{env('DOOM_DIR')}", f"{targetDir}", f"{target}", f"{target}.wad"))


def nextFile(filePath, extension):
    number = 0
    result = f"{filePath}_{stringNumber(number, 3)}{extension}"

    while os.path.exists(f"{result}"):
        number += 1
        result = f"{filePath}_{stringNumber(number, 3)}{extension}"

    return result, number


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


def getTime(label="Start: "):
    current = datetime.datetime.now().replace(microsecond = 0)
    print(f"{label}{current.strftime('%H:%M:%S')}")
    return current


def readJson(filePath):
    with open(filePath) as contents:
        return json.load(contents)


def readMods(configuration, sourceDir, targetWad):
    modKeys = [ "music", "mods" ]

    if not configuration:
        raise ValueError("Won't load mods with non-existent configuration.")
    if not os.path.exists(sourceDir):
        raise ValueError(f"No such mod source directory: {sourceDir}.")
    if not targetWad:
        raise ValueError("Can't read mods for a non-target.")

    if targetWad not in configuration:
        return []

    result = []
    for modKey in modKeys:
        if modKey not in configuration[targetWad]:
            continue

        result = []
        for file in configuration[targetWad][modKey]:
            fullPath = os.path.join(sourceDir, file)

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
    _addon              = []
    _attempts           = -1
    _category           = ""
    _command            = ""
    _compatibility      = ""
    _configuration      = {}
    _configurationPath  = ""
    _demo               = -1
    _demoPath           = ""
    _difficulty         = SKILLS["uv"]
    _doLaunch           = True
    _executable         = env("GZDOOM_EXE")
    _fast               = False
    _files              = []
    _iwad               = "doom2"
    _iwadPath           = ""
    _listAttempts       = True
    _map                = ""
    _mapper             = ""
    _modDir             = ""
    _mods               = ""
    _noMonsters         = False
    _player             = env("DOOM_PLAYER")
    _practice           = False
    _respawn            = False
    _settings           = {}
    _skill              = ""
    _target             = ""
    _targetPath         = ""
    _warp               = ""
    _useMods            = True
    _verbose            = False
    _version            = env("GZDOOM_LATEST_VERSION")

    def __init__(self,
                 category,
                 compatibility,
                 demo,
                 configuration,
                 doLaunch,
                 executable,
                 fast,
                 files,
                 listAttempts,
                 map,
                 mapper,
                 noMonsters,
                 player,
                 practice,
                 respawn,
                 skill,
                 target,
                 useMods,
                 verbose,
                 version):

        addonPath         = os.path.join(os.path.dirname(self._executable), "addon")
        executablePath    = str(executable)
        modPath           = os.path.join(os.path.dirname(self._executable), "mod")
        skill, difficulty = SKILLS[str(skill)]
        targetPath        = getPWad(target, mapper)

        self._addon             = verifyDir(addonPath)
        self._configurationPath = verifyFile(configuration)
        self._executablePath    = verifyFile(executablePath)
        self._modDir            = verifyDir(modPath)
        self._targetPath        = verifyFile(targetPath)

        self._category      = str(category).lower()
        self._compatibility = str(compatibility).lower()
        self._difficulty    = str(difficulty).lower()
        self._demo          = int(demo)
        self._doLaunch      = bool(doLaunch)
        self._fast          = bool(fast)
        self._files         = list(files)
        self._listAttempts  = bool(listAttempts)
        self._mapper        = str(mapper).title()
        self._noMonsters    = bool(noMonsters)
        self._player        = str(player).title()
        self._practice      = bool(practice)
        self._respawn       = bool(respawn)
        self._skill         = str(skill).lower()
        self._target        = str(target).lower()
        self._version       = str(version).lower()
        self._useMods       = bool(useMods)
        self._verbose       = bool(verbose)

        self._settings[ARG_TO_SETTING["--fast"]]          = self._fast
        self._settings[ARG_TO_SETTING["--nomonsters"]]    = self._noMonsters
        self._settings[ARG_TO_SETTING["--respawn"]]       = self._respawn

        self._command         = "-record" if self._demo < 0 else "-playdemo"
        self._configuration   = readJson(self._configurationPath)
        self._executable      = os.path.basename(self._executablePath).split(".")[0]
        self._iwad            = getIWad(self._configuration, target)
        self._iwadPath        = verifyFile(os.path.join(env("DOOM_IWAD_DIR"), self._iwad, f"{self._iwad}.wad"))
        self._map, self._warp = parseMap(map, self._iwad)
        self._mods            = readMods(self._configuration, self._modDir, self._target) + autoLoad(self._addon)

        self._files += self._mods
        if self._iwad != self._target:
            self._files.append(self._targetPath)

        self._demoPath, self._attempts = demoFileSetup(self._executable,
                                                       self._version,
                                                       self._player,
                                                       self._mapper,
                                                       self._target,
                                                       self._map,
                                                       self._difficulty,
                                                       self._category,
                                                       self._settings,
                                                       self._demo)

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

        extraLine = ""
        prefix = ""
        for flag, setting in self._settings.items():
            if setting:
                extraLine = f"{extraLine}{prefix}{flag}"
                prefix = " "

        if extraLine and extraLine != "":
            lines.append(f"        Settings:    {extraLine}")

        if self._doLaunch and not self._practice:
            lines.append(f"        {self.demoCommand()}      {self.demoPath()}")

        return "\n".join(lines)

    def demoCommand(self):
        return self._command

    def demoPath(self):
        return self._demoPath

    def executable(self):
        return self._executable

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

        for flag, setting in self._settings.items():
            if setting:
                result.extend([flag])

        if not self._practice:
            result.extend([self.demoCommand(), self.demoPath()])

        if self._attempts >= 0 and self._listAttempts:
            print(f"| Attempt:     #{self._attempts}.")

        start = getTime(label = "| Start:       ")
        if not self._doLaunch and not self._verbose:
            print(" ".join(result))
            exitCode = 0
        else:
            exitCode = subprocess.call(result)
        total = getTime(label = "| Finish:      ") - start
        print(f"| Total:       {total}")

        if self._demoPath:
            print(f"Wrote demo to: {self.demoPath()}")

        return exitCode

    def executablePath(self):
        return self._executablePath

    def compatibility(self):
        return self._compatibility

    def difficulty(self):
        return self._difficulty

    def files(self):
        return self._files

    def iwad(self):
        return self._iwad

    def iwadPath(self):
        return self._iwadPath

    def practice(self):
        return self._practice

    def target(self):
        return self._target

    def targetPath(self):
        return self._targetPath

    def skill(self):
        return self._skill

    def warp(self):
        return [str(number) for number in self._warp]


def readLaunch(argv):
    parser = argparse.ArgumentParser(prog = "DOOM Launcher", description = "DOOM Launcher Helper")
    parser.add_argument("target")

    parser.add_argument("-a", "--fast",             action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Play with fast monsters.")

    parser.add_argument("-b", "--noAttempts",       action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Don't list attempt count for current map.")

    parser.add_argument("-c", "--category",         default = "max",
                                                    help    = "Type of map completion type.")

    parser.add_argument("-d", "--demo",             default = -1,
                                                    help    = "Run demo; argument is demo number.")

    parser.add_argument("-e", "--executable",       default = env("GZDOOM_EXE"),
                                                    help    = "Executable to use.")

    parser.add_argument("-f", "--files",            default = [],
                                                    help    = "Extra files; use for testing.",
                                                    nargs   = "*")

    parser.add_argument("-g", "--configuration",    default = os.path.join(os.path.dirname(sys.argv[0]), "../pwads.json"),
                                                    help    = "Configuration file to use.")

    parser.add_argument("-i", "--practice",         action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Don't record demo.")

    parser.add_argument("-m", "--map",              default = "1",
                                                    help    = "Map number.",
                                                    nargs   = "+")

    parser.add_argument("-n", "--nomonsters",       action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Play without monsters.")

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

    parser.add_argument("-w", "--respawn",          action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Play with respawning monsters.")

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
        fast          = result.fast,
        files         = result.files,
        listAttempts  = not result.noAttempts,
        map           = result.map,
        mapper        = result.mapper,
        noMonsters    = result.nomonsters,
        player        = result.player,
        practice      = result.practice,
        respawn       = result.respawn,
        skill         = result.skill,
        target        = result.target,
        useMods       = not result.unmodded,
        verbose       = result.verbose,
        version       = result.version,
    )


if __name__ == "__main__":
    sys.exit(readLaunch(sys.argv[1:]).execute())
