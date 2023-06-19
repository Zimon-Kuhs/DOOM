import os

if __name__ == "__main__":
    directory = os.path.dirname(__file__)
    for subDir in os.listdir(directory):
        if not os.path.isdir(subDir):
            continue

        mapName = os.path.basename(subDir)
        print(mapName)
        for file in os.listdir(subDir):
            if file == os.path.basename(__file__):
                continue

            sourceDir = os.path.join(directory, subDir)
            number = file.split("_")[1].split(".")[0]

            # leftParts = file.split("_")
            # rightParts = leftParts[1].split(".")
            # right = rightParts[1]

            # number = rightParts[0]
            # oldNumber = str(number)

            while len(number) < 3:
                number = f"0{number}"

            source = os.path.join(sourceDir, file)
            destination = os.path.join(sourceDir, f"Cinnamon-tnt-{mapName}-uv-max_{number}.lmp")
            # print(f"    {source}    ->    {destination}")
            os.rename(source, destination)
