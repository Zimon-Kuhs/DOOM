raise NotImplementedError(f"{__file__} is not implemented.")

import getopt
import os
import sys

from web import readWiki
import monster


def usage(scriptName = os.path.basename(__file__), exitCode = 0):
    """
        Print usage and exit.

        @param exitCode The exit code to return.
    """

    print(f"{scriptName} HOST")
    sys.exit(exitCode)


if __name__ == "__main__":

    optlist, args = [], []

    try:
        optlist, args = getopt.getopt(sys.argv[1:], "pu:")
    except getopt.GetoptError as error:
        usage()

    target = None
    website = None
    for opt, value in optlist:
        if opt == "-p":
            target = "HP"
        elif opt == "-u":
            website = value
        else:
            usage()

    data = readWiki.levelData(website)
    monsters = monster.parse("data/monsters.json")

    hp = {}
    for monster, amounts in data["Monsters"].items():
        hp[monster] = amounts[-1] * monsters[monster].hp()

    print(sum([value for _, value in hp.items()]))
