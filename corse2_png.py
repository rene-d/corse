#!/usr/bin/env python3

from math import cos, sin

# relevé des points dans l'image corse1.png
from corse1_png import POINTS as corse_raw


def rotate(x, y, angle):
    c, s = cos(angle), sin(angle)
    return round(c * x + s * y), round(-s * x + c * y)


def affine(x, y, a, v):
    return a * x + v[0], y * a + v[1]


# adapte les points à corse2.png
POINTS = list(rotate(*affine(x, y, 1.49, (29, -21)), -0.073) for x, y in corse_raw)

if __name__ == "__main__":
    print(POINTS)
