# Monocraft, a monospaced font for developers who like Minecraft a bit too much.
# Copyright (C) 2022-2023 Idrees Hassan
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import json
import math
import os

import fontforge

from generate_continuous_ligatures import generate_continuous_ligatures
from generate_diacritics import generateDiacritics
from generate_examples import generateExamples
from polygonizer import PixelImage, generatePolygons

PIXEL_SIZE = 120

characters = json.load(open("./characters.json"))
diacritics = json.load(open("./diacritics.json"))
ligatures = json.load(open("./ligatures.json"))
ligatures += generate_continuous_ligatures("./continuous_ligatures.json")

characters = generateDiacritics(characters, diacritics)
charactersByCodepoint = {}


def generateFont():
    monocraft = fontforge.font()
    monocraft.fontname = "Monocraft"
    monocraft.familyname = "Monocraft"
    monocraft.fullname = "Monocraft"
    monocraft.copyright = "Idrees Hassan, https://github.com/IdreesInc/Monocraft"
    monocraft.encoding = "UnicodeFull"
    monocraft.version = "3.0"
    monocraft.weight = "Regular"
    monocraft.ascent = PIXEL_SIZE * 8
    monocraft.descent = PIXEL_SIZE
    monocraft.em = PIXEL_SIZE * 9
    monocraft.upos = -PIXEL_SIZE  # Underline position
    monocraft.addLookup(
        "ligatures",
        "gsub_ligature",
        (),
        (("liga", (("dflt", ("dflt")), ("latn", ("dflt")))),),
    )
    monocraft.addLookupSubtable("ligatures", "ligatures-subtable")

    for character in characters:
        charactersByCodepoint[character["codepoint"]] = character
        monocraft.createChar(character["codepoint"], character["name"])
        pen = monocraft[character["name"]].glyphPen()
        top = 0
        drawn = character

        image, kw = generateImage(character)
        drawImage(image, pen, **kw)
        monocraft[character["name"]].width = PIXEL_SIZE * 6
    print(f"Generated {len(characters)} characters")

    outputDir = "../dist/"
    if not os.path.exists(outputDir):
        os.makedirs(outputDir)

    monocraft.generate(outputDir + "Monocraft-no-ligatures.ttf")
    for ligature in ligatures:
        lig = monocraft.createChar(-1, ligature["name"])
        pen = monocraft[ligature["name"]].glyphPen()
        image, kw = generateImage(ligature)
        drawImage(image, pen, **kw)
        monocraft[ligature["name"]].width = PIXEL_SIZE * len(ligature["sequence"]) * 6
        lig.addPosSub(
            "ligatures-subtable",
            tuple(
                map(
                    lambda codepoint: charactersByCodepoint[codepoint]["name"],
                    ligature["sequence"],
                )
            ),
        )
    print(f"Generated {len(ligatures)} ligatures")

    monocraft.generate(outputDir + "Monocraft.ttf")
    monocraft.generate(outputDir + "Monocraft.otf")


def generateImage(character):
    image = PixelImage()
    kw = {}
    if "pixels" in character:
        arr = character["pixels"]
        leftMargin = character["leftMargin"] if "leftMargin" in character else 0
        x = math.floor(leftMargin)
        kw["dx"] = leftMargin - x
        descent = -character["descent"] if "descent" in character else 0
        y = math.floor(descent)
        kw["dy"] = descent - y
        image = image | imageFromArray(arr, x, y)
    if "reference" in character:
        other = generateImage(charactersByCodepoint[character["reference"]])
        kw.update(other[1])
        image = image | other[0]
    if "diacritic" in character:
        diacritic = diacritics[character["diacritic"]]
        arr = diacritic["pixels"]
        x = image.x
        y = findHighestY(image) + 1
        if "diacriticSpace" in character:
            y += int(character["diacriticSpace"])
        image = image | imageFromArray(arr, x, y)
    return (image, kw)


def findHighestY(image):
    for y in range(image.y_end - 1, image.y, -1):
        for x in range(image.x, image.x_end):
            if image[x, y]:
                return y
    return image.y


def imageFromArray(arr, x=0, y=0):
    return PixelImage(
        x=x,
        y=y,
        width=len(arr[0]),
        height=len(arr),
        data=bytes(x for a in reversed(arr) for x in a),
    )


def drawImage(image, pen, *, dx=0, dy=0):
    for polygon in generatePolygons(image):
        start = True
        for x, y in polygon:
            x = (x + dx) * PIXEL_SIZE
            y = (y + dy) * PIXEL_SIZE
            if start:
                pen.moveTo(x, y)
                start = False
            else:
                pen.lineTo(x, y)
        pen.closePath()


generateFont()
generateExamples(characters, ligatures, charactersByCodepoint)
