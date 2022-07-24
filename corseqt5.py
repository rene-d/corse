#!/usr/bin/env python3

import sys

import numpy as np
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QPolygon
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget

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


def rotate(x, y, angle):
    c, s = np.cos(angle), np.sin(angle)
    j = np.matrix([[c, s], [-s, c]])
    m = np.dot(j, [x, y])
    return round(m.A1[0]), round(m.A1[1])


class LineLabel(QLabel):
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0
    flag = False
    move_event = None
    info_event = None
    points = QPolygon(QPoint(*rotate(x / 1.045 - 7, y / 1.045 - 130, -0.073)) for x, y in corse_raw)

    def __init__(self, parent):
        super().__init__(parent)
        self.setMouseTracking(True)

    def mousePressEvent(self, event):
        self.flag = True
        self.x0 = event.x()
        self.y0 = event.y()

    def mouseReleaseEvent(self, event):
        self.flag = False
        if self.info_event:
            self.info_event(f"Longueur: {round(np.sqrt((self.x1 - self.x0) ** 2 + (self.y1 - self.y0) ** 2))}")

    def mouseMoveEvent(self, event):
        if self.flag:
            self.x1 = event.x()
            self.y1 = event.y()
            self.update()

        if self.move_event:
            self.move_event(event.x(), event.y())

    def paintEvent(self, event):
        super().paintEvent(event)
        with QPainter(self) as painter:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawLine(self.x0, self.y0, self.x1, self.y1)
            painter.drawPolygon(self.points)


class Contour(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q:
            self.close()

    def initUI(self):
        self.setWindowTitle("Contour de la Corse")

        pixmap = QPixmap("corse2.png")
        pixmap = pixmap.scaled(1200, 1200, Qt.KeepAspectRatio)

        self.contour = LineLabel(self)
        self.contour.setPixmap(pixmap)
        self.contour.setCursor(Qt.CrossCursor)

        lay = QVBoxLayout(self)
        lay.addWidget(self.contour)

        lay2 = QHBoxLayout()

        self.coords_label = QLabel(self)
        self.coords_label.setText("Coordonnées")
        lay2.addWidget(self.coords_label)

        self.info_label = QLabel(self)
        self.info_label.setText("Segments")
        lay2.addWidget(self.info_label)

        lay.addLayout(lay2)

        self.contour.move_event = lambda x, y: self.coords_label.setText("Coordonnées: ( %d , %d )" % (x, y))
        self.contour.info_event = lambda x: self.info_label.setText(x)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    x = Contour()
    sys.exit(app.exec_())
