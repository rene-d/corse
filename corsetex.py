#!/usr/bin/env python3

# rene-d 2020/07/23

import argparse
import subprocess
from pathlib import Path

import numpy as np

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

mire_raw = [
    (0, 0),
    (0, 1),
    (1, 1),
    (1, 0),
]


def rotate(xy, radians):
    x, y = xy
    c, s = np.cos(radians), np.sin(radians)
    j = np.matrix([[c, s], [-s, c]])
    m = np.dot(j, [x, y])
    r_xy = float(m.T[0]), float(m.T[1])
    return np.array(r_xy)


def tikz_draw_line(tikz, points, color, thickness="0.5pt", dotted=False):
    xy = " -- ".join(f"({p[0]},{p[1]})" for p in points)
    tikz.append(rf"\draw[{'dotted,' if dotted else ''}line width={thickness},color={color}] {xy};")


def tikz_image(corse, thickness, details=True):

    assert min(x for x, _ in corse) == 0
    assert min(y for _, y in corse) == 0

    picture = []
    infos = []

    picture.append(
        r"""
\newcommand{\corse}[4]{
\begin{tikzpicture}[line cap=round,line join=round,x=10mm,y=10mm]
\clip({(#1-0.5)},{(#2-0.5)}) rectangle ({(#3+0.5)},{(#4+0.5)});
\draw [dashdotted,line width=1pt,color=black] ({(#1-0.5)},{(#2-0.5)}) rectangle ({(#3+0.5)},{(#4+0.5)});
\node [rectangle,text=lightgray] (r) at ({((#1+#3)/2)},{((#2+#4)/2)}) {\Huge Page \thepage};
\draw [dashed,line width=0.1pt,color=gray] (#1,#2) rectangle (#3,#4);
"""
    )
    # dessine le contour
    picture.append(rf"\draw [line width=1pt,color=cyan]")
    for p in corse:
        picture.append(f"({p[0]},{p[1]}) --")
    picture.append("  cycle;")

    # pour écrire les informations sur chaque segment/sommet
    infos.append(["N", "X", "Y", "Length", "Angle", "Cut"])

    angles = []
    total_length = 0

    for i, p in enumerate(corse):
        # sommet du contour
        p1 = p
        p2 = corse[(i + 1) % len(corse)]
        p3 = corse[(i + 2) % len(corse)]

        v1 = np.array(p1) - np.array(p2)
        v2 = np.array(p3) - np.array(p2)

        angle = np.math.atan2(np.linalg.det([v1, v2]), np.dot(v1, v2))
        angles.append(angle)

        # informations de découpe
        angle_degrees = np.degrees(angle)
        length = np.linalg.norm(v1)

        total_length += length

        # calcul angle de coupe
        if angle_degrees >= 0:
            cut_angle_degrees = angle_degrees / 2  # angle saillant
        else:
            cut_angle_degrees = 180 + angle_degrees / 2  # angle rentrant

        infos.append(
            map(
                str,
                (
                    i + 1,
                    round(p[0] * 10, 1),
                    round(p[1] * 10, 1),
                    round(length * 10, 1),
                    round(angle_degrees, 1),
                    round(cut_angle_degrees, 1),
                ),
            )
        )

    interior = []  # bord intérieur

    for i, p in enumerate(corse):

        # points origine et extrémité
        p1 = p
        p2 = corse[(i + 1) % len(corse)]

        # affiche le numéro du segment
        if details:
            xy_middle = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
            picture.append(rf"\draw[color=black] ({xy_middle[0]},{xy_middle[1]}) node[rectangle,draw,fill=white] {{\tiny ${1+i}$}};")

        # angles origine/extrémité
        a1 = angles[(i - 1) % len(corse)]
        a2 = angles[i]

        v = np.array(p1) - np.array(p2)
        u = v / np.linalg.norm(v) * thickness

        # traits de construction (pour vérifier les calculs!)
        r = rotate(u, -np.pi / 2)
        if details:
            tikz_draw_line(picture, [p1, (*(r + p1),), (*(r + p2),), p2], color="black", dotted=True)

        if a2 >= 0:
            color = "red"  # coupe angle aigu
        else:
            color = "green"  # coupe angle obtus

        # trace le trait de coupe
        xy = rotate(u / np.sin(a2 / 2), -a2 / 2) + p2
        xy = (*xy,)
        if details:
            tikz_draw_line(picture, [p2, xy], color=color, thickness="0.25pt")
        interior.append(xy)

        if details:
            p_angle = p2
            angle = np.degrees(a2)
            picture.append(rf"\draw[color=violet] ({p_angle[0]},{p_angle[1]}) node[] {{\small ${angle:.0f}$\textdegree}};")

    # dessine le contour intérieur
    if details:
        picture.append(rf"\draw [densely dotted,line width=0.5pt,color=black]")
        for p in interior:
            picture.append(f"({p[0]},{p[1]}) --")
        picture.append("  cycle;")

    picture.append(r"\end{tikzpicture}")
    picture.append("}")
    picture.append("")

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
    mid_length = mid_length / 2

    max_x = max(x for x, _ in corse)
    max_y = max(y for _, y in corse)

    dimensions = [round(max_x, 2), round(max_y, 2), round(mid_length, 1), round(mid_length + len(infos) * 0.2, 1)]

    return "\n".join(picture), infos, dimensions


def tikz_corse(picture, x1, y1, col, row, landscape=True):

    page = rf"\corse{{{x1*col}}}{{{y1*row}}}{{{x1*(col+1)}}}{{{y1*(row+1)}}}"

    if landscape:
        return r"\newpage\begin{landscape}" + page + r"\end{landscape}"
    else:
        return r"\newpage" + page


def calcule(width, thickness, show_details=False, model_raw=corse_raw, output_file=None):

    page_x, page_y = 27, 18

    # recalcule les coordonnées des points dans l'image
    min_x = min(x for x, _ in model_raw)
    max_x = max(x for x, _ in model_raw)
    min_y = min(y for _, y in model_raw)
    max_y = max(y for _, y in model_raw)
    scale_width = 1 / (max_x - min_x) * width
    model = []
    for x, y in model_raw:
        x = (x - min_x) * scale_width
        y = (y - min_y) * scale_width
        model.append((x, y))

    picture_command, infos, (dim_x, dim_y, mean_length, mean_length_real) = tikz_image(model, thickness, show_details)

    preambule = r"""\documentclass[a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage{textcomp}
\usepackage{tikz}
\usepackage[margin=0mm]{geometry}
\usepackage{pdflscape}
\usepackage{pgfplotstable}
\usepackage{graphicx}

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

        for x in range(nb_x):
            for y in range(nb_y):
                cmd = tikz_corse(picture_command, page_y, page_x, x, y, landscape)
                print(cmd)
                document.append(cmd)

    else:
        nb_x = np.math.ceil(dim_x / page_x)
        nb_y = np.math.ceil(dim_y / page_y)
        landscape = True

        for x in range(nb_x):
            for y in range(nb_y):
                cmd = tikz_corse(picture_command, page_x, page_y, x, y, landscape)
                print(cmd)
                document.append(cmd)

    # document.append(tikz_corse(picture_command, page_x, page_y, 0, 0, True))

    document.append(r"\newpage\subsection*{Dimensions}")
    document.append(f"Taille : {dim_x} cm $\\times$ {dim_y} cm\\newline")
    document.append(f"Ratio x/y: {round(dim_x/dim_y,4)}\\newline")
    document.append(f"Longueur moyenne: {mean_length} cm\\newline")
    document.append(f"Longueur profilé: {mean_length_real} cm (avec trait de coupe 2 mm)\\newline")

    document.append(f"Cadre : {page_x} cm $\\times$ {page_y} cm\\newline")

    document.append(
        r"""\subsection*{Segments}
\pgfplotstabletypeset[
	col sep=comma,
	every head row/.style={before row=\hline,after row=\hline},
	every last row/.style={after row=\hline},
	every first column/.style={column type/.add={|}{|}},
	every last column/.style={column type/.add={}{|}},
	columns/Length/.style = {column type/.add={|}{|}}
]{
"""
    )
    for info in infos:
        document.append(",".join(info))
    document.append("}")

    document.append(r"\section*{} {\color{gray} Made with {\ensuremath\heartsuit} in Corsica}")
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
        if not Path("/.dockerenv").exists():
            subprocess.run(["open", "corse.pdf"])
    except subprocess.CalledProcessError:
        pass

def main():

    parse = argparse.ArgumentParser(
        description="Calcule les angles et longueurs du contour de <épaisseur> mm pour une longueur totale de <échelle> mm"
    )
    parse.add_argument("-c", "--contour", action="store_true", help="affiche le contour uniqument")
    parse.add_argument("-o", "--output", type=Path, default="corse.pdf", help="fichier PDF")
    parse.add_argument(
        "size",
        metavar="échelle",
        type=float,
        nargs="?",
        default=25,
        help="hauteur du modèle en cm",
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

    # calcule(args.size, args.thickness / 10, not args.contour, mire_raw)
    calcule(args.size, args.thickness / 10, not args.contour, output_file= args.output)


if __name__ == "__main__":
    main()
