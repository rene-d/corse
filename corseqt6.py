#!/usr/bin/env python3
# rene-d 2022

import argparse
import json
import math
import sys
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QKeySequence, QPainter, QPen, QPixmap, QPolygon, QShortcut, QMouseEvent
from PySide6.QtWidgets import QApplication, QFileDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget


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

    def __init__(self, parent, points):
        super().__init__(parent)
        self.default_points = points
        self.points = QPolygon(self.default_points)
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
        if self.edit_mode and self.edit_point >= 0 and self.points.size() > 2:
            self.points.remove(self.edit_point)
            self.edit_point = -1
            self.update()

    def save_points(self, path: Path):
        with path.open("w") as f:
            json.dump(list((p.x(), p.y()) for p in self.points), f)

    def reset(self):
        self.points = QPolygon(self.default_points)
        self.edit_mode = False
        self.measure_mode = False
        self.update()

    def load_points(self, path: Path):
        self.default_points = list([QPoint(*p) for p in json.loads(path.read_text())])
        self.reset()

    def mousePressEvent(self, event: QMouseEvent):
        self.flag = True
        self.x0 = event.position().toPoint().x()
        self.y0 = event.position().toPoint().y()

        if self.edit_mode and self.insert_point >= 0:
            self.points.insert(self.insert_point, event.position().toPoint())
            self.edit_point = self.insert_point
            self.insert_point = -1

    def mouseReleaseEvent(self, event: QMouseEvent):
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

    def mouseMoveEvent(self, event: QMouseEvent):
        if self.flag:
            if self.edit_mode:
                if self.edit_point >= 0:
                    self.points[self.edit_point] = event.position().toPoint()
            else:
                self.x1 = event.position().toPoint().x()
                self.y1 = event.position().toPoint().y()
            self.update()

        elif self.edit_mode:

            prev_p = self.points[-1]
            self.edit_point = -1
            self.insert_point = -1

            for i, p in enumerate(self.points):
                if (p - event.position().toPoint()).manhattanLength() < 5:
                    self.edit_point = i
                    self.setCursor(Qt.SizeAllCursor)
                    self.info_event(f"Edit point: {i}")
                    break

                if ((p + prev_p) / 2 - event.position().toPoint()).manhattanLength() < 5:
                    self.insert_point = i
                    self.setCursor(Qt.SplitHCursor)
                    self.info_event(f"Add point: {i}")
                    break

                prev_p = p

            else:
                self.info_event("Edit mode")
                self.unsetCursor()

        if self.move_event:
            self.move_event(event.position().toPoint())

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
    def __init__(self, image_path: Path, points_path: Path = None):
        super().__init__()
        self.image_path = image_path
        self.points_path = points_path or self.image_path.with_suffix(".json")
        self.initUI()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Q or event.key() == Qt.Key_Escape:
            self.close()

    def initUI(self):
        self.setWindowTitle(f"Contour de {self.image_path.stem}")

        pixmap = QPixmap(self.image_path.as_posix())
        pixmap = pixmap.scaled(1200, 1200, Qt.KeepAspectRatio)

        if self.points_path.exists():
            points = list([QPoint(*p) for p in json.loads(self.points_path.read_text())])
        else:
            r = pixmap.rect()
            x_sixth = r.width() // 6
            y_half = r.height() // 2
            points = list((QPoint(x_sixth, y_half), QPoint(r.width() - x_sixth, y_half)))

        self.contour = LineLabel(self, points)
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

        self.contour.move_event = lambda pos: self.coords_label.setText("Coordonnées: ( %d , %d )" % (pos.x(), pos.y()))
        self.contour.info_event = lambda x: self.info_label.setText(x)

        QShortcut(QKeySequence(Qt.Key_E), self, activated=self.contour.toggle_edit)
        QShortcut(QKeySequence(Qt.Key_Backspace), self, activated=self.contour.delete_point)
        QShortcut(QKeySequence(Qt.Key_S), self, activated=self.save_points)
        QShortcut(QKeySequence(Qt.Key_R), self, activated=self.contour.reset)
        QShortcut(QKeySequence(Qt.Key_L), self, activated=self.load_points)

        self.show()

    def save_points(self):
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Enregistrer le contour de {self.image_path.stem}",
            self.points_path.as_posix(),
            "JSON (*.json)",
            options=QFileDialog.DontConfirmOverwrite | QFileDialog.DontUseNativeDialog,
        )
        if filename:
            filename = Path(filename)
            if filename.suffix == "":
                filename = filename.with_suffix(".json")
            self.contour.save_points(filename)
            print(f"Points enregistrés dans {filename}")
            self.points_path = filename

    def load_points(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            f"Chrger le contour de {self.image_path.stem}",
            "",
            "JSON (*.json)",
            options=QFileDialog.DontUseNativeDialog,
        )
        if filename:
            filename = Path(filename)
            if filename.is_file():
                self.contour.load_points(Path(filename))


if __name__ == "__main__":

    parse = argparse.ArgumentParser(
        description="Tracé d'un contour",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=30),
    )
    parse.add_argument("-i", "--image", type=Path, help="image", default="corse.png")
    parse.add_argument("-p", "--points", type=Path, help="fichier des points")
    args = parse.parse_args()

    app = QApplication(sys.argv)
    x = Contour(args.image, args.points)
    sys.exit(app.exec())
