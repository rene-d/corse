#!/usr/bin/env python3
# rene-d 2022

import math
import json
from pathlib import Path
import sys

from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QPen, QPixmap, QPolygon, QKeySequence
from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QVBoxLayout, QWidget, QShortcut

# points dans l'image corse2.png
from corse2_png import POINTS


class LineLabel(QLabel):
    x0 = 0
    y0 = 0
    x1 = 0
    y1 = 0
    flag = False
    move_event = None
    info_event = None
    points = QPolygon()
    measure_mode = True
    edit_mode = False
    edit_point = -1
    insert_point = -1

    def __init__(self, parent):
        super().__init__(parent)
        if Path("corse2.json").exists():
            with Path("corse2.json").open() as f:
                self.points = QPolygon(
                    [QPoint(*p) for p in json.load(f)]
                )
        else:
            self.points = QPolygon(QPoint(x, y) for x, y in POINTS)
        self.setMouseTracking(True)

    def toggle_edit(self):
        self.edit_mode = not self.edit_mode
        self.info_event(f"Edit mode: {self.edit_mode}")
        self.update()

        if self.edit_mode:
            self.measure_mode = False
        else:
            self.unsetCursor()

    def delete_point(self):
        if self.edit_mode and self.edit_point >= 0:
            self.points.remove(self.edit_point)
            self.edit_point = -1
            self.update()

    def save_points(self):
        with open("corse2.json", "w") as f:
            json.dump(list((p.x(), p.y()) for p in self.points), f)

    def reset(self):
        self.points = QPolygon(QPoint(x, y) for x, y in POINTS)
        self.edit_mode=False
        self.measure_mode=False
        self.update()

    def mousePressEvent(self, event):
        self.flag = True
        self.x0 = event.x()
        self.y0 = event.y()

        if self.edit_mode and self.insert_point >= 0:
            self.points.insert(self.insert_point, QPoint(event.x(), event.y()))
            self.edit_point = self.insert_point
            self.insert_point = -1

    def mouseReleaseEvent(self, event):
        self.flag = False
        if self.edit_mode:
            pass

        else:
            self.measure_mode = True
            self.info_event(
                f"L: {round(math.sqrt((self.x1 - self.x0) ** 2 + (self.y1 - self.y0) ** 2),1)}"
                + f" | H: {abs(self.x1 - self.x0)}"
                + f" | V: {abs(self.y1 - self.y0)}"
                + f" | θ: {round(math.degrees(math.atan2(self.y1 - self.y0, self.x1 - self.x0)), 1)}°"
            )

    def mouseMoveEvent(self, event):
        if self.flag:
            if self.edit_mode:
                if self.edit_point >= 0:
                    self.points[self.edit_point] = QPoint(event.x(), event.y())
            else:
                self.x1 = event.x()
                self.y1 = event.y()
            self.update()

        elif self.edit_mode:

            prev_p = self.points[-1]
            self.edit_point = -1
            self.insert_point = -1

            for i, p in enumerate(self.points):
                if (p - event.pos()).manhattanLength() < 5:
                    self.edit_point = i
                    self.setCursor(Qt.SizeAllCursor)
                    self.info_event(f"Edit point: {i}")
                    break

                if ((p + prev_p) / 2 - event.pos()).manhattanLength() < 5:
                    self.insert_point = i
                    self.setCursor(Qt.SplitHCursor)
                    self.info_event(f"Add point: {i}")
                    break

                prev_p = p

            else:
                self.info_event("Edit mode")
                self.unsetCursor()

        if self.move_event:
            self.move_event(event.x(), event.y())

    def paintEvent(self, event):
        super().paintEvent(event)
        with QPainter(self) as painter:
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
            painter.drawPolygon(self.points)

            if self.edit_mode:
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))

                prev_p = self.points[-1]
                for p in self.points:
                    painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                    painter.drawEllipse(p, 5, 5)
                    painter.setPen(QPen(Qt.yellow, 2, Qt.SolidLine))
                    painter.drawEllipse((p + prev_p) / 2, 5, 5)
                    prev_p = p

            elif self.measure_mode:
                painter.setPen(QPen(Qt.blue, 2, Qt.SolidLine))
                painter.drawLine(self.x0, self.y0, self.x1, self.y1)


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

        QShortcut(QKeySequence(Qt.Key_E), self, activated=self.contour.toggle_edit)
        QShortcut(QKeySequence(Qt.Key_Backspace), self, activated=self.contour.delete_point)
        QShortcut(QKeySequence(Qt.Key_S), self, activated=self.contour.save_points)
        QShortcut(QKeySequence(Qt.Key_R), self, activated=self.contour.reset)

        self.show()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    x = Contour()
    sys.exit(app.exec_())
