import requests


def text(url):
    return requests.get(url).text


def removeTags(text, tags):
    result = text
    for tag in tags:
        result = result.replace(f"<{tag}>", "").replace(f"</{tag}>", "")
    return result


def categorize(raw):
    stop = "Multiplayer"
    categories = [
        "Monsters",
        "Weapons",
        "Ammunition",
        "Health &amp; Armor",
        "Items",
        "Key",
        "Miscellaneous",
        stop
    ]

    result = { name: [] for name in categories}
    lines = raw.splitlines()

    line = None
    lineIndex = 0
    categoryIndex = 0
    currentCategory = None
    nextCategory = categories[categoryIndex]

    while lineIndex < len(lines):
        line = lines[lineIndex]

        if nextCategory in line:
            if categoryIndex + 1 >= len(categories):
                break

            currentCategory = nextCategory
            categoryIndex += 1
            nextCategory = categories[categoryIndex]

        if currentCategory:
            result[currentCategory].append(line)

        lineIndex += 1

    del result[stop]
    return result


def adjust(text, adjustments):
    result = text

    for pre, post in adjustments:
        result = result.replace(pre, post)
    return result

def lexical(text):
    result = []
    for word in text.split():
        result.append(word[0].upper() + word[1:].lower())

    return " ".join([new for new in result])


def readCategory(values):
    result = {}
    currentName = None
    stops = ["</table>"]

    for line in values[6:]:
        pruned = removeTags(line, ["td", "th", "tr", "td colspan=\"3\""])

        if any([test in line for test in stops]):
            break

        if not pruned:
            currentName = None
            continue

        if not currentName:
            if "a href" in pruned:
                currentName = pruned.split("/wiki/")[1].split("\" title")[0]
            else:
                currentName = pruned.replace("<td style=\"text-align: left;\">", "")

            currentName = lexical(currentName.replace("_", " ").replace("%27", "'"))
            currentName = adjust(currentName, [["Of", "of"], ["Bfg", "BFG"], ["-vile", "-Vile"]])
            result[currentName] = []
            continue

        result[currentName].append(int(pruned))

    return result



def levelData(url):
    single = {
        "Monsters": {},
        "Weapons": {},
        "Ammunition": {},
        "Health & Armor": {},
        "Items": {},
        "Keys": {},
        "Miscellaneous": {}
    }

    for name, value in categorize(text(url)).items():
        single[name] = readCategory(value)

    return single
