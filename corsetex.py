#!/usr/bin/env python3
# rene-d 2022

import argparse
from curses import def_prog_mode
import json
import subprocess
from pathlib import Path

import numpy as np


def rotate(xy, radians):
    c, s = np.cos(radians), np.sin(radians)
    j = np.matrix([[c, s], [-s, c]])
    m = np.dot(j, xy)
    r_xy = float(m.T[0]), float(m.T[1])
    return np.array(r_xy)


def tikz_draw_line(tikz, points, color, thickness="0.5pt", style=None, cycle=False):
    xy = "\n -- ".join(f"({p[0]},{p[1]})" for p in points)
    if cycle:
        xy += "\n -- cycle"
    if style:
        style += ","
    else:
        style = ""
    tikz.append(rf"\draw[{style}line width={thickness},color={color}] {xy};")


def orientation(polygon):
    """
    Détermination orientation du polygone.
    [principe](https://fr.wikipedia.org/wiki/Orientation_de_courbe)
    """

    # sélection du point
    x_max = 0
    y_max = 0
    i_max = None
    for i, p in enumerate(polygon):
        x, y = p
        if x >= x_max:
            x_max = x
            if y >= y_max:
                y_max = y
                i_max = i

    # matrice d'orientation
    p1 = polygon[(i_max - 1) % len(polygon)]
    p2 = polygon[i_max]
    p3 = polygon[(i_max + 1) % len(polygon)]

    o = np.array([[1, p1[0], p1[1]], [1, p2[0], p2[1]], [1, p3[0], p3[1]]])

    return 1 if np.linalg.det(o) >= 0 else -1


def tikz_image(corse, thickness, details=True):

    assert min(x for x, _ in corse) == 0
    assert min(y for _, y in corse) == 0

    sens = orientation(corse)

    picture = []
    infos = []

    picture.append(
        r"""
\newcommand{\corse}[4]{
\begin{tikzpicture}[line cap=round,line join=round,x=10mm,y=10mm]
\clip({(#1-0.5)},{(#2-0.5)}) rectangle ({(#3+0.5)},{(#4+0.5)});
\draw[dashdotted,line width=1pt,color=black] ({(#1-0.5)},{(#2-0.5)}) rectangle ({(#3+0.5)},{(#4+0.5)});
\node[rectangle,text=lightgray] (r) at ({((#1+#3)/2)},{((#2+#4)/2)}) {\Huge Page \thepage};
\draw[dashed,line width=0.1pt,color=gray] (#1,#2) rectangle (#3,#4);"""
    )

    # dessine le contour
    picture.append("% contour")
    tikz_draw_line(picture, corse, color="cyan", thickness="1pt", cycle=True)

    angles = []
    total_length = 0

    for i, p in enumerate(corse):
        # sommet du contour
        p1 = p
        p2 = corse[(i + 1) % len(corse)]
        p3 = corse[(i + 2) % len(corse)]

        v1_2 = np.array(p1) - np.array(p2)
        v2_3 = np.array(p3) - np.array(p2)

        angle = np.math.atan2(np.linalg.det([v1_2, v2_3]), np.dot(v1_2, v2_3))
        angles.append(angle)

        # informations de découpe
        angle_degrees = np.degrees(angle)
        length = np.linalg.norm(v1_2)

        total_length += length

        # calcul angle de coupe
        if angle_degrees >= 0:
            cut_angle_degrees = angle_degrees / 2  # angle saillant
        else:
            cut_angle_degrees = 180 + angle_degrees / 2  # angle rentrant

        infos.append(
            (
                i + 1,
                round(p1[0] * 10, 1),
                round(p1[1] * 10, 1),  # coordonnées début du segment
                round(length * 10, 1),  # longueur du segment
                round(angle_degrees, 1),  # angle avec le segment suivant
                round(cut_angle_degrees, 1),  # angle de coupe
            )
        )

    interior = []  # bord intérieur

    if details:

        for i, p in enumerate(corse):

            picture.append(f"% segment {i + 1}")

            # points origine et extrémité
            p1 = p
            p2 = corse[(i + 1) % len(corse)]

            # angles origine/extrémité
            a1 = angles[(i - 1) % len(corse)]
            a2 = angles[i]

            v = (np.array(p2) - np.array(p1)) * sens
            u = v / np.linalg.norm(v) * thickness

            # affiche le numéro du segment
            if np.linalg.norm(v) > 1:
                xy_middle = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
                picture.append(rf"\draw[color=black] ({xy_middle[0]},{xy_middle[1]}) node[rectangle,draw,fill=white] {{\tiny ${1+i}$}};")

            # traits de construction (pour vérifier les calculs!)
            r = rotate(u, -np.pi / 2)
            tikz_draw_line(picture, [p1, (*(r + p1),), (*(r + p2),), p2], color="black", style="dotted")

            if a2 >= 0:
                color = "red"  # coupe angle aigu
            else:
                color = "green"  # coupe angle obtus

            xy = rotate(u / np.sin(a2 / 2), -a2 / 2) + p2
            xy = (*xy,)
            interior.append(xy)

            # trace le trait de coupe [a,b]
            a = p2
            b = xy
            ab = np.array(xy) - np.array(p2)
            ab = ab / np.linalg.norm(ab)

            tikz_draw_line(picture, [a - ab * 0.3, b + ab * 0.5], color=color, thickness="0.25pt")

            # angle du contour
            p_angle = a - ab * 0.4
            angle = np.degrees(a2)
            picture.append(rf"\draw[color=violet] ({p_angle[0]},{p_angle[1]}) node[] {{\tiny ${angle:.0f}$\textdegree}};")

        # dessine le contour intérieur
        picture.append("% contour intérieur")
        tikz_draw_line(picture, interior, color="black", thickness="0.5pt", style="densely dotted", cycle=True)

    picture.append(r"\end{tikzpicture}")
    picture.append("}")
    picture.append("")

    # la longueur du profilé est la longueur moyenne:
    # - chaque bord est un trapèze, la surface du trapèze est (l1+l2)*h/2
    # - la longueur du profilé est la surface du contour divisée par l'épaisseur
    # - la surface du contour est la somme des surfaces des trapèzes, soit (∑(l1+l2))*h/2
    # - et donc la longueur du profilé est ∑(l1+l2)/2
    length_contour = 0
    for i in range(len(corse)):
        p1 = corse[i]
        p2 = corse[(i + 1) % len(corse)]
        v1_2 = np.array(p1) - np.array(p2)
        length_contour += np.linalg.norm(v1_2)

    length_interior = 0
    for i in range(len(interior)):
        p1 = interior[i]
        p2 = interior[(i + 1) % len(corse)]
        v2_3 = np.array(p1) - np.array(p2)
        length_interior += np.linalg.norm(v2_3)

    if len(interior) > 0:
        mid_length = (length_contour + length_interior) / 2
    else:
        mid_length = length_contour

    max_x = max(x for x, _ in corse)
    max_y = max(y for _, y in corse)

    dimensions = [round(max_x, 2), round(max_y, 2), round(length_contour, 1), round(mid_length + len(infos) * 0.2, 1), len(corse)]

    return "\n".join(picture), infos, dimensions


def tikz_corse(picture, x1, y1, col, row, landscape=True):

    page = rf"\corse{{{x1*col}}}{{{y1*row}}}{{{x1*(col+1)}}}{{{y1*(row+1)}}}"

    if landscape:
        return r"\newpage\begin{landscape}" + page + r"\end{landscape}"
    else:
        return r"\newpage" + page


def calcule(width, thickness, points, show_details=False, output_file=None, recto=False):

    page_x, page_y = 27, 18

    # recalcule les coordonnées des points dans l'image
    min_x = min(x for x, _ in points)
    max_x = max(x for x, _ in points)
    min_y = min(y for _, y in points)
    max_y = max(y for _, y in points)
    scale_width = 1 / (max_x - min_x) * width
    model = []
    for x, y in points:
        x = (x - min_x) * scale_width

        # Nota: le polygone est censé être à l'endroit dans le repère de l'écran (0,0) en haut à gauche
        # et donc à l'envers dans un repère mathématique classique comme celui utilisé par TikZ
        if recto:
            y = (max_y - y) * scale_width
        else:
            y = (y - min_y) * scale_width

        model.append((x, y))

    picture_command, infos, (dim_x, dim_y, mean_length, mean_length_real, segments) = tikz_image(model, thickness, show_details)

    preambule = r"""\documentclass[a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{textcomp}
\usepackage{tikz}
\usepackage[margin=0mm]{geometry}
\usepackage{pdflscape}
\usepackage{pgfplotstable}
\usepackage{graphicx}
\usepackage{colortbl}
\usepackage{multicol}

\pgfplotsset{compat=1.18}
\pagestyle{empty}
\geometry{left=10mm,top=10mm,right=0mm,bottom=0mm,paperwidth=210mm,paperheight=297mm}
"""

    document = []
    document.append(r"\begin{document}")

    print("dims", dim_x, dim_y)
    print("page", page_x, page_y)

    if dim_y % page_x >= page_y:
        nb_x = np.math.ceil(dim_x / page_y)
        nb_y = np.math.ceil(dim_y / page_x)
        landscape = False

        for y in range(nb_y):
            for x in range(nb_x):
                cmd = tikz_corse(picture_command, page_y, page_x, x, y, landscape)
                print("page", 1 + x + y * nb_x, cmd)
                document.append(cmd)

    else:
        nb_x = np.math.ceil(dim_x / page_x)
        nb_y = np.math.ceil(dim_y / page_y)
        landscape = True

        for y in range(nb_y):
            for x in range(nb_x):
                cmd = tikz_corse(picture_command, page_x, page_y, x, y, landscape)
                print("page", 1 + x + y * nb_x, cmd)
                document.append(cmd)

    document.append(r"\newpage\subsection*{Dimensions}")
    document.append(f"Taille : {dim_x} cm $\\times$ {dim_y} cm\\newline")
    document.append(f"Ratio x/y : {round(dim_x/dim_y,4)}\\newline")
    document.append(f"Longueur contour : {mean_length} cm ({segments} segments)\\newline")
    document.append(f"Longueur profilé : {mean_length_real} cm (longueur moyenne + trait de coupe 2 mm)\\newline")

    document.append(f"Cadre : {page_x} cm $\\times$ {page_y} cm")

    document.append(
        r"""\subsection*{Segments}
\textit{Les angles sont donnés pour l'extrémité de fin du segment (donc avec le segment suivant).}
"""
    )
    document.append(r"\begin{multicols*}{3}\noindent")

    for col in range(0, len(infos), 40):
        document.append(
            r"""\pgfplotstabletypeset[
	col sep=comma,
	every head row/.style={before row=\hline,after row=\hline},
	every last row/.style={after row=\hline},
	every first column/.style={column type/.add={|}{|}},
	every last column/.style={column type/.add={}{|}},
    every even row/.style={before row={\rowcolor[gray]{0.93}}},
	columns/Longueur/.style = {column type/.add={}{|}},
	columns/Angle/.style = {column type/.add={}{|}}
]{"""
        )
        document.append(r"N,Longueur,Angle,Coupe")

        for i, info in enumerate(infos[col : col + 40]):
            prev_info = infos[(i - 1) % len(infos)]
            line = map(
                str,
                (
                    info[0],  # numéro
                    # info[1],
                    # info[2],  # coordonnées début
                    info[3],  # longueur
                    # prev_info[4],
                    # prev_info[5],  # angles avec le segment précédent
                    info[4],
                    info[5],  # angles avec le segment suivant
                ),
            )
            document.append(",".join(line))
        document.append("}")
        document.append("")

    document.append(r"\end{multicols*}")

    # document.append(r"\section*{} {\color{gray} Made with {\ensuremath\heartsuit} in Corsica}")
    document.append(r"\end{document}")

    with Path("corse.tex").open("wt") as f:
        f.write(preambule)
        f.write(picture_command)
        f.write("\n".join(document))

    try:
        subprocess.check_call(["texfot", "latex", "-output-format=pdf", "-interaction=nonstopmode", "corse.tex"])
        if output_file and output_file.absolute() != Path("corse.pdf").absolute():
            output_file.write_bytes(Path("corse.pdf").read_bytes())
    except subprocess.CalledProcessError as e:
        print(e)
        exit(2)

    try:
        if not Path("/.dockerenv").exists() and not output_file:
            subprocess.run(["open", "corse.pdf"])
    except subprocess.CalledProcessError:
        pass


def main():

    parse = argparse.ArgumentParser(
        description="Calcule les angles et longueurs du contour de <épaisseur> mm pour une longueur totale de <taille> cm",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30),
    )
    parse.add_argument("-c", "--contour", action="store_true", help="affiche le contour uniqument")
    parse.add_argument("-r", "--recto", action="store_true", help="affiche le recto (verso par défaut)")
    parse.add_argument("-p", "--points", type=Path, help="fichier de points", default="corse2.json")
    parse.add_argument("-o", "--output", type=Path, help="fichier PDF généré")
    parse.add_argument(
        "size",
        metavar="taille",
        type=float,
        nargs="?",
        default=27,
        help="taille du modèle en cm",
    )
    parse.add_argument(
        "thickness",
        metavar="épaisseur",
        type=float,
        nargs="?",
        default=10,
        help="épaisseur profilé en mm",
    )

    args = parse.parse_args()

    if args.points.exists():
        points = json.loads(args.points.read_text())
    else:
        parse.error(f"{args.points} does not exist")

    calcule(args.size, args.thickness / 10, points, not args.contour, output_file=args.output, recto=args.recto)


if __name__ == "__main__":
    main()
