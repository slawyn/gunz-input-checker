
from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QApplication
from PyQt5.QtGui import QPainter, QPen, QFont, QBrush
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QRectF
from PyQt5.QtChart import QChart, QChartView, QLineSeries

class RectangleWidget(QWidget):
    RECT_SIZE = 60

    def __init__(self, text, subtext="", parent=None, is_red=False):
        super().__init__(parent)
        self.text = text
        self.subtext = subtext  # Use subtext instead of text
        self.is_red = is_red
        if is_red:
            self.setFixedSize(RectangleWidget.RECT_SIZE*3, RectangleWidget.RECT_SIZE)  # Adjust the size as needed
        else:
            self.setFixedSize(RectangleWidget.RECT_SIZE, RectangleWidget.RECT_SIZE)  # Adjust the size as needed

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.is_red:
            painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        else:
            painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        painter.drawRect(rect)

        font = QFont()
        font.setPointSize(8)
        painter.setPen(QPen(Qt.red))
        painter.setFont(font)

        painter.drawText(QRectF(10, 10, self.width() - 20, (self.height() - 20) / 2),
                         Qt.AlignCenter,
                         self.text)
        painter.drawText(QRectF(10, 30, self.width() - 20, (self.height() - 20) / 2),
                         Qt.AlignCenter,
                         self.subtext)
