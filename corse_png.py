#!/usr/bin/env python3

from math import cos, sin

# relevé des points dans l'image corse1.png
corse_raw = [
    (745, 135),  # Bonifacio
    (596, 81),
    (484, 88),
    (415, 47),  # Aleria
    (220, 70),
    (181, 98),
    (114, 91),
    (27, 114),
    (33, 145),
    (109, 149),
    (124, 139),  # Nonza
    (175, 148),  # Saint-Florent
    (151, 174),
    (151, 207),
    (187, 230),
    (215, 298),  # Algajola
    (255, 338),  # ajouté
    (329, 378),
    (365, 326),
    (383, 376),
    (428, 359),  # Cargese
    (460, 305),
    (502, 353),
    (529, 343),  # Sanguinaires
    (516, 285),  # Ajaccio
    (591, 314),
    (617, 242),  # Propriano
    (652, 282),
    (699, 228),
    (712, 170),
    (733, 171),
]


def rotate(x, y, angle):
    c, s = cos(angle), sin(angle)
    return round(c * x + s * y), round(-s * x + c * y)


def affine(x, y, a, v):
    return a * x + v[0], y * a + v[1]


# adapte les points à corse.png pour une largeur de 1200 pixels
POINTS = list(rotate(*affine(x, y, 1.49, (29, -21)), -0.073) for x, y in corse_raw)

if __name__ == "__main__":
    from argparse import ArgumentParser
    from json import dumps
    from pathlib import Path

    image_path = Path(__file__).with_name(Path(__file__).stem.replace("_", "."))
    points_path = image_path.with_suffix(".json")

    parse = ArgumentParser(description=f"Points du contour de {image_path.name}")
    parse.add_argument("-j", "--json", action="store_true", help="affiche les points en JSON")
    parse.add_argument("-o", "--output", type=Path, help="fichier de points")
    parse.add_argument("-O", action="store_true", help=f"crée le fichier {points_path.name}")
    args = parse.parse_args()
    if args.O:
        points_path.write_text(dumps(POINTS))
    else:
        if args.output:
            output = args.output.write_text
        else:
            output = print
        if args.json:
            output(dumps(POINTS))
        else:
            output(str(POINTS))
