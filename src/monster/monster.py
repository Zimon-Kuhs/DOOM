import json
import sys

from web import page


def getOptional(dictionary, key):
    return dictionary[key] if key in dictionary else None


class Monster:

    def __init__(self, name, stats):
        self.myName = name
        self.myHp = getOptional(stats, "HP")
        self.myModifiers = getOptional(stats, "Modifiers")

    def hp(self):
        return self.myHp

    def modifiers(self):
        return self.myModifiers

    def stats(self):
        return {
            "HP": self.myHp,
            "Modifiers": self.myModifiers
        }

    def name(self):
        return self.myName


def copyMonsters(monsterData, copies):
    toAdd = []

    for name, stats in copies.items():
        monster = monsterData[stats["Copy Of"]]
        toAdd.append(Monster(name, monster.stats()))

    for addition in toAdd:
        monsterData[addition.name()] = addition


def readMonsters(monsterData):
    copies = {}
    result = {}

    for game in monsterData:
        for name in monsterData[game]:
            stats = monsterData[game][name]

            if "Copy Of" in stats:
                copies[name] = stats
            else:
                result[name] = Monster(name, stats)

    return result, copies if len(copies) > 0 else None


def parse(filePath):
    data = None
    with open(filePath, "r", encoding = "utf-8") as contents:
        data = json.load(contents)


    monsters, copies = readMonsters(data)

    if copies:
        copyMonsters(monsters, copies)

    return monsters
