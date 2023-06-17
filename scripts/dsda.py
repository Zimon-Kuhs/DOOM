import argparse
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

CATEGORY_KEY = {
    "collector":    "col",
    "fast":         "f",
    "max":          "m",
    "nomo":         "o",
    "nomo100":      "os",
    "speed":        "",
    "nightmare":    "n",
    "nightmare100": "s",
    "pacifist":     "p",
    "respawn":      "r",
    "stroller":     "str",
    "tyson":        "t",
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


def demoFileSetup(executable, version, player, mapper, target, short, mapData, difficulty, category, settings, demo):
    dirBase  = os.path.join(env("DOOM_DEMO_DIR"), executable, version, player)

    if mapper is not None and mapper != "":
        dirBase = os.path.join(dirBase, ".test", mapper)

    demoDir  = os.path.join(dirBase, target, mapData)

    mapPart      = mapData[2:] if len(mapData) == 1 else mapData
    skillPart    = "" if difficulty == "uv" else SKILLS[difficulty][1][:2]
    wadPart      = (short if short else target)
    wadPart      = wadPart if wadPart not in [ "doom", "doom2" ] else ""
    categoryPart = CATEGORY_KEY[category] + "".join([CATEGORY_KEY[setting] for setting, value in settings.items() if value])

    demoFile = "".join([ wadPart, mapPart, skillPart, categoryPart ])

    fullPath = f"{os.path.join(demoDir, demoFile)}-HHMMSS.lmp"
    result = fullPath
    if demo is None or demo == "":

        if os.path.exists(result):
            raise ValueError(f"File for -record already exists. {result}")

        os.makedirs(demoDir, exist_ok = True)

    else:
        if not isinstance(demo, str) or not demo.isnumeric():
            raise ValueError(f"Demo number should be numeric string: {demo} ({type(demo)}).")

        result = f"{fullPath}_{stringNumber(demo, 3)}.lmp"

        if not os.path.exists(result):
            raise ValueError(f"File for -playdemo doesn't exist. {result}")

    return f"{result}"


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

    if not configuration:
        raise ValueError("Won't load mods with non-existent configuration.")
    if not os.path.exists(sourceDir):
        raise ValueError(f"No such mod source directory: {sourceDir}.")
    if not targetWad:
        raise ValueError("Can't read mods for a non-target.")

    if targetWad not in configuration or modKey not in configuration[targetWad]:
        return []

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
    _executable        = env("DSDA_EXE")
    _fast              = False
    _files             = []
    _iwad              = "doom2"
    _iwadPath          = ""
    _map               = ""
    _mapper            = ""
    _modDir            = ""
    _mods              = ""
    _modifiers         = {}
    _noMonsters        = False
    _player            = env("DOOM_PLAYER")
    _respawn           = False
    _settings          = {}
    _skill             = ""
    _short             = ""
    _target            = ""
    _targetPath        = ""
    _warp              = ""
    _useMods           = True
    _verbose           = False
    _version           = env("DSDA_LATEST_VERSION")

    def __init__(self,
                 category,
                 compatibility,
                 demo,
                 configuration,
                 doLaunch,
                 executable,
                 fast,
                 files,
                 map,
                 mapper,
                 noMonsters,
                 player,
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
        self._demo          = str(demo)
        self._doLaunch      = bool(doLaunch)
        self._fast          = bool(fast)
        self._files         = list(files)
        self._mapper        = str(mapper).title()
        self._noMonsters    = bool(noMonsters)
        self._player        = str(player).title()
        self._respawn       = bool(respawn)
        self._skill         = str(skill).lower()
        self._target        = str(target).lower()
        self._version       = str(version).lower()
        self._useMods       = bool(useMods)
        self._verbose       = bool(verbose)

        self._modifiers[ARG_TO_SETTING["--fast"]]          = self._fast
        self._modifiers[ARG_TO_SETTING["--nomonsters"]]    = self._noMonsters
        self._modifiers[ARG_TO_SETTING["--respawn"]]       = self._respawn

        self._command         = "-record" if not self._demo else "-playdemo"
        self._configuration   = readJson(self._configurationPath)
        self._executable      = os.path.basename(self._executablePath).split(".")[0]
        self._iwad            = getIWad(self._configuration, target)
        self._iwadPath        = verifyFile(os.path.join(env("DOOM_IWAD_DIR"), self._iwad, f"{self._iwad}.wad"))
        self._map, self._warp = parseMap(map, self._iwad)
        self._mods            = readMods(self._configuration, self._modDir, self._target) + autoLoad(self._addon)
        self._short           = self._configuration["short"] if "short" in self._configuration else ""

        self._files += self._mods
        if self._iwad != self._target:
            self._files.append(self._targetPath)

        self._demoPath = demoFileSetup(self._executable,
                                       self._version,
                                       self._player,
                                       self._mapper,
                                       self._target,
                                       self._short,
                                       self._map,
                                       self._difficulty,
                                       self._category,
                                       self._modifiers,
                                       self._demo)

    def __str__(self):
        commandString = self.demoCommand()
        commandString = commandString + ("" if len(commandString) == 9 else "  ")

        lines = ["Launch commands:"]
        lines.append(f"    executable: {self.executablePath()}")
        lines.append(f"        -complevel:  {self.compatibility()}")

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
        result.extend(["-complevel", self.compatibility()])
        result.extend(["-iwad", self.iwadPath()])
        result.extend(["-file"] + self.files())
        result.extend(["-skill", self.skill()])
        result.extend(["-warp"] + self.warp())

        for flag, setting in self._settings.items():
            if setting:
                result.extend([flag])

        result.extend([self.demoCommand(), self.demoPath()])

        if self._doLaunch:
            return subprocess.call(result)
        else:
            print(" ".join(result))

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

    parser.add_argument("-c", "--category",         default = "max",
                                                    help    = "Type of map completion type.")

    parser.add_argument("-d", "--demo",             default = "",
                                                    help    = "Run demo; argument is demo number.")

    parser.add_argument("-e", "--executable",       default = env("DSDA_EXE"),
                                                    help    = "Executable to use.")

    parser.add_argument("-f", "--files",            default = [],
                                                    help    = "Extra files; use for testing.",
                                                    nargs   = "*")

    parser.add_argument("-g", "--configuration",    default = os.path.join(os.path.dirname(sys.argv[0]), "pwads.json"),
                                                    help    = "Configuration file to use.")

    parser.add_argument("-m", "--map",              default = "1",
                                                    help    = "Map number.",
                                                    nargs   = "+")

    parser.add_argument("-n", "--nomonsters",       action  = "store_const",
                                                    const   = True,
                                                    default = False,
                                                    help    = "Play without monsters.")

    parser.add_argument("-o", "--compatibility",    default = None,
                                                    help    = "Compatibility setting (complevel).")

    parser.add_argument("-p", "--player",           help    = "Player name.",
                                                    default = env("DOOM_PLAYER"))

    parser.add_argument("-r", "--version",          default = env("DSDA_LATEST_VERSION"),
                                                    help    = "DSDA version.")

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
        map           = result.map,
        mapper        = result.mapper,
        noMonsters    = result.nomonsters,
        player        = result.player,
        respawn       = result.respawn,
        skill         = result.skill,
        target        = result.target,
        useMods       = not result.unmodded,
        verbose       = result.verbose,
        version       = result.version,
    )


if __name__ == "__main__":
    sys.exit(readLaunch(sys.argv[1:]).execute())
