#!/usr/bin/env python3

# rene-d 2020/07/23

from sys import argv
import operator
from PIL import Image, ImageDraw, ImageFont, ImageTk
import numpy as np

import csv
import argparse
import tkinter as tk


# relevé des points dans l'image corse1.png
corse_raw = [
    (1198, 324),  # Bonifacio
    (966, 239),
    (791, 250),
    (684, 186),  # Aleria
    (380, 222),
    (319, 265),
    (214, 255),
    (79, 291),
    (88, 339),
    (207, 345),
    (230, 329),  # Nonza
    (310, 344),  # Saint-Florent
    (272, 385),
    (272, 435),
    (328, 471),
    (372, 578),  # Algajola
    (435, 640),  # ajouté
    (550, 702),
    (606, 621),
    (634, 699),
    (705, 672),  # Cargese
    (754, 588),
    (820, 664),
    (862, 648),  # Sanguinaires
    (842, 557),  # Ajaccio
    (958, 603),
    (999, 491),  # Propriano
    (1053, 552),
    (1127, 469),
    (1147, 378),
    (1180, 380),
]

croix_raw = [
    (0, 1125),
    (400, 1125),
    (400, 1510),
    (600, 1510),
    (600, 1125),
    (1000, 1125),
    (1000, 915),
    (600, 915),
    (600, 0),
    (400, 0),
    (400, 915),
    (0, 915),
]


def rotate(xy, radians):
    c, s = np.cos(radians), np.sin(radians)
    j = np.matrix([[c, s], [-s, c]])
    m = np.dot(j, xy)
    r_xy = float(m.T[0]), float(m.T[1])
    return np.array(r_xy)


def calcule(
    width,
    thickness,
    show_background=False,
    precision=1,
    min_x=37,
    min_y=113,
    max_x=1247,
    max_y=774,
    ratio_x=1,
    ratio_y=1,
    corse_raw=corse_raw,
):

    corse = [(x * ratio_x, y * ratio_y) for x, y in corse_raw]

    min_x, min_y = (min_x * ratio_x, min_y * ratio_y)
    max_x, max_y = (max_x * ratio_x, max_y * ratio_y)

    if show_background:
        # image = Image.open("1000px-Corse_region_location_map.svg.png")
        # image = Image.open("Corse_region_relief_location_map.jpg")
        image = Image.open("corse1.png")
    else:
        # image = Image.new("RGB", size=(1972, 1000), color=(255, 255, 255))
        image = Image.new("RGB", size=(776, 424), color=(255, 255, 255))

    image = image.resize((1972 * precision, 1000 * precision), Image.Resampling.BICUBIC)

    font_number = ImageFont.truetype("HelveticaNeue.ttc", 16 * precision)
    font_angle = ImageFont.truetype("HelveticaNeue.ttc", 20 * precision)
    font_fixed = ImageFont.truetype("Menlo", 17 * precision)

    # recalcule les coordonnées des points dans l'image
    image_width, image_height = image.size
    corse2 = []
    for xy in corse:
        x, y = xy
        x = round((x - min_x) / (max_x - min_x) * image_width)
        y = round((y - min_y) / (max_y - min_y) * image_height)
        corse2.append((x, y))
    corse = corse2

    # dimensions max de la Corse en pixels
    dim_x = max(map(operator.itemgetter(0), corse)) - min(map(operator.itemgetter(0), corse))
    dim_y = max(map(operator.itemgetter(1), corse)) - min(map(operator.itemgetter(1), corse))

    # ajuste le coefficient d'échelle
    scale = width / dim_x

    # contexte PIL pour dessiner dans l'image
    draw = ImageDraw.Draw(image)

    # cartouche pour les dimensions
    info = f"n°  long. angle coupe"
    text_width, text_height = draw.textsize(info, font=font_fixed)
    draw.rectangle(
        (
            0,
            image_height - 1 - (len(corse) + 1) * text_height,
            text_width + 2,
            image_height,
        ),
        outline=(0, 0, 0),
        width=1,
        fill=(255, 255, 255),
    )
    draw.text(
        (1, image_height - 1 - (len(corse) + 1) * text_height),
        info,
        font=font_fixed,
        fill=(255, 0, 0),
    )

    # dessine le contour
    corse.append(corse[0])
    draw.line(corse, fill=(128, 128, 255), width=8)
    corse.pop()

    # pour écrire les informations sur chaque segment/sommet
    csv_writer = csv.writer(open("sommets.csv", "w"))

    angles = []
    total_length = 0

    for i, p in enumerate(corse):
        p1 = p
        p2 = corse[(i + 1) % len(corse)]
        p3 = corse[(i + 2) % len(corse)]

        xy_middle = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2

        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)

        u1 = v1 / np.linalg.norm(v1)
        u2 = v2 / np.linalg.norm(v2)

        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        angles.append(angle)

        angle = np.degrees(angle)
        length = np.linalg.norm(v1) * scale

        total_length += length

        if angle >= 0:
            cut_angle = angle / 2  # angle saillant
        else:
            cut_angle = 180 + angle / 2  # angle rentrant

        print(f"{(i + 1):2d} l={length:6.1f} 𝛼={angle:6.1f}° cut={cut_angle:6.1f}°")

        info = f"{(i + 1):2d} {length:6.1f} {angle:4.0f}° {cut_angle:4.0f}°"
        draw.text(
            (1, image_height - 1 - (len(corse) - i) * text_height),
            info,
            font=font_fixed,
            fill=(0, 0, 0),
        )

        row = [
            i + 1,
            round(p[0] * scale, 1),
            round(p[1] * scale, 1),
            round(length, 1),
            round(angle, 1),
            round(cut_angle, 1),
        ]
        csv_writer.writerow(row)

        sz = draw.textsize(f"{i + 1}", font=font_number)
        draw.rectangle(
            (
                xy_middle[0] - sz[0] / 2 - 2,
                xy_middle[1] - sz[1] / 2 - 2,
                xy_middle[0] + sz[0] / 2 + 2,
                xy_middle[1] + sz[1] / 2 + 2,
            ),
            fill=(255, 255, 255),
            outline=(0, 0, 0),
            width=1,
        )

        draw.text(
            (xy_middle[0] - sz[0] / 2, xy_middle[1] - sz[1] / 2),
            f"{i + 1}",
            align="center",
            fill=(0, 0, 0),
            font=font_number,
        )

        draw.text(p2, f"{angle:.0f}°", align="center", fill=(0, 0, 0), font=font_angle)

        draw.point(p1, fill=(0, 0, 0))

    interior = []  # bord intérieur

    for i, p in enumerate(corse):

        # points origine et extrémité
        p1 = p
        p2 = corse[(i + 1) % len(corse)]

        # angles origine/extrémité
        a1 = angles[(i - 1) % len(corse)]
        a2 = angles[i]

        v = np.array(p1) - np.array(p2)
        u = v / np.linalg.norm(v) * thickness / scale

        # traits de construction (pour vérifier les calculs!)
        r = rotate(u, -np.pi / 2)
        draw.line([p1, *(r + p1)], fill=(0, 0, 0))
        draw.line([p2, *(r + p2)], fill=(0, 0, 0))
        draw.line([*(r + p1), *(r + p2)], fill=(0, 0, 0))

        if a2 >= 0:
            color = (255, 0, 0)  # coupe angle aigu
        else:
            color = (0, 255, 0)  # coupe angle obtus

        # trace le trait de coupe
        xy = rotate(u / np.sin(a2 / 2), -a2 / 2) + p2
        draw.line([p2, *xy], fill=color)

        interior.append((*xy,))

    interior.append(interior[0])
    draw.line(interior, fill=(0, 0, 0), width=2)
    interior.pop()

    # la longueur du profilé est la longueur moyenne:
    # - chaque bord est un trapèze, la surface du trapèze est (l1+l2)*h/2
    # - la longueur du profilé est la surface du contour divisée par l'épaisseur
    # - la surface du contour est la somme des surfaces des trapèzes, soit (∑(l1+l2))*h/2
    # - et donc la longueur du profilé est ∑(l1+l2)/2
    mid_length = 0
    for i in range(len(corse)):
        p1 = corse[i]
        p2 = corse[(i + 1) % len(corse)]
        v1 = np.array(p1) - np.array(p2)

        p1 = interior[i]
        p2 = interior[(i + 1) % len(corse)]
        v2 = np.array(p1) - np.array(p2)
        mid_length += np.linalg.norm(v1) + np.linalg.norm(v2)
    mid_length = mid_length / 2 * scale

    print(f"overall width:  {width} mm")
    print(f"outline length: {total_length:.0f} mm")
    print(f"profile length: {mid_length:.0f} mm (thickness: {thickness} mm)")
    # print(f"minimum length: {mid_length + thickness * 2 + len(corse) * 1.6:.0f} mm")
    print(f"image size: {image.size}")

    # dimensions Corse et longueur du contour
    info = f"dim: {dim_x*scale:.1f} x {dim_y*scale:.1f}\ncontour: {total_length:.0f}\nthickness: {thickness}"
    tw, th = draw.textsize(info, font=font_fixed)
    draw.text(
        ((image_width - tw) / 2, (image_height - th) / 2),
        info,
        fill=(0, 0, 0),
        font=font_fixed,
        align="center",
    )

    return image


def show_model(width=1972, height=1000):
    # min_x = 0
    # min_y = 0

    root = tk.Tk()

    # root.attributes('-fullscreen', True)

    canvas = tk.Canvas(root, borderwidth=0, highlightthickness=0)
    canvas.grid(row=0, column=0, sticky="nsew")

    view = None
    image = None

    def upd():
        nonlocal view, canvas, image

        print("x", canvas.winfo_width())
        print(canvas.winfo_width())

        image = calcule(915, 20, True, 1)
        sz = image.size
        print(sz)
        image = image.convert(mode="RGB")
        image = image.resize(map(int, (1972 / 2, 1000 / 2)), Image.Resampling.BICUBIC)
        image = ImageTk.PhotoImage(image)

        if not view:
            view = tk.Label(canvas, image=image)
            view.pack()
        else:
            view.configure(image=image)

    def callback(event):
        # nonlocal min_x, min_y

        if event.type == tk.EventType.Motion:
            return
        print(event)

        if event.keysym == "Escape" or event.keysym == "q" or event.keysym == "x":
            root.destroy()
        # elif event.keysym == "Right":
        #     min_x += 1
        # elif event.keysym == "Left":
        #     min_x -= 1
        # elif event.keysym == "Up":
        #     min_y -= 1
        # elif event.keysym == "Down":
        #     min_y += 1
        elif event.keysym == "u":
            upd()

    root.bind("<Key>", callback)
    root.bind("<Motion>", callback)

    upd()

    root.mainloop()


def main():

    parse = argparse.ArgumentParser(
        description="Calcule les angles et longueurs du contour de <épaisseur> mm pour une longueur totale de <échelle> mm"
    )
    parse.add_argument("-m", "--model", action="store_true", help="affiche le modèle en fond")
    parse.add_argument(
        "scale",
        metavar="échelle",
        type=float,
        nargs="?",
        default=915,
        help="hauteur du modèle en mm",
    )
    parse.add_argument(
        "thickness",
        metavar="épaisseur",
        type=float,
        nargs="?",
        default=20,
        help="épaisseur profilé en mm",
    )

    args = parse.parse_args()

    if args.model:
        show_model()
    else:
        # image = calcule(args.scale, args.thickness, args.model, 2, corse_raw=[(x/4+300,600-y/4) for x,y in croix_raw])
        image = calcule(args.scale, args.thickness, args.model, 2)
        image.show("Corse")

        image.putalpha(128)
        image.save("c.png")


if __name__ == "__main__":
    main()
