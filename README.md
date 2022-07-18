# Corse

## Synopsis

Calcule les longueurs et angles de découpe du contour de la Corse.

## Usage

```text
usage: corsetex.py [-h] [-c] [-o OUTPUT] [échelle] [épaisseur]

Calcule les angles et longueurs du contour de <épaisseur> mm pour une longueur totale de <échelle> cm

positional arguments:
  échelle               taille du modèle en cm
  épaisseur             épaisseur profilé en mm

options:
  -h, --help            show this help message and exit
  -c, --contour         affiche le contour uniqument
  -o OUTPUT, --output OUTPUT
                        fichier PDF
```

## Prérequis

[LaTeX](https://www.tug.org/texlive/), [Pillow](https://python-pillow.org), [numpy](https://numpy.org)
