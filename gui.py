from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QApplication
from PyQt5.QtGui import QPainter, QPen, QFont, QBrush
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QRectF
import time


class Entry:
    def __init__(self, text, subtext):
        self.subtext = subtext
        self.text = text

    def __str__(self):
        return f"{self.text} ({self.subtext})"


class Entries:
    def __init__(self, name=""):
        self.name = name
        self.entries = []

    def set_name(self, name):
        self.name = name

    def add(self, text, subtext):
        self.entries.append(Entry(text, subtext))

    def __str__(self):
        return f"{self.name}: {[str(entry) for entry in self.entries]}"


class Worker(QObject):
    finished = pyqtSignal()
    add_rectangle = pyqtSignal(list, str)  # Additional parameter of type string

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def run(self):
        while self.handler.is_running():
            time.sleep(0.001)
            if entries := self.handler.run():
                self.add_rectangle.emit(entries.entries, entries.name)  # Emit additional parameter

        self.finished.emit()


class RectangleWidget(QWidget):
    def __init__(self, text, subtext="", parent=None, is_red=False):
        super().__init__(parent)
        self.text = text
        self.subtext = subtext  # Use subtext instead of text
        self.is_red = is_red
        if is_red:
            self.setFixedSize(200, 70)  # Adjust the size as needed
        else:
            self.setFixedSize(70, 70)  # Adjust the size as needed

    def paintEvent(self, event):
        painter = QPainter(self)
        if self.is_red:
            painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))  # Fill with red
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        else:
            painter.setBrush(Qt.NoBrush)  # No fill for non-red rectangles
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        painter.drawRect(rect)

        font = QFont()
        font.setPointSize(12)
        painter.setPen(QPen(Qt.blue))
        painter.setFont(font)

        text_rect = QRectF(10, 10, self.width() - 20, (self.height() - 20) / 2)
        subtext_rect = QRectF(10, 30, self.width() - 20, (self.height() - 20) / 2)

        painter.drawText(text_rect, Qt.AlignCenter, self.text)
        painter.drawText(subtext_rect, Qt.AlignCenter, self.subtext)


class Gui(QMainWindow):
    SPACING = 0
    WIDGET_HEIGHT = 50

    def __init__(self, handler):
        super().__init__()
        self.setWindowTitle("Scrollable Qt5 Window")
        self.setGeometry(100, 100, 1000, 800)
        self.closeCallback = handler.stop

        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(Gui.SPACING)
        self.content_layout.setContentsMargins(10, 10, 10, Gui.SPACING)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)

        self.setCentralWidget(self.scroll_area)

        self.thread = QThread()
        self.worker = Worker(handler)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.add_rectangle.connect(self.add_rectangle)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def add_rectangle(self, entries, name):
        hbox_layout = QHBoxLayout()
        hbox_layout.setAlignment(Qt.AlignLeft)
        if name:
            red_widget = RectangleWidget(name, "", self, is_red=True)
            hbox_layout.addWidget(red_widget)
        for entry in entries:
            rect_widget = RectangleWidget(entry.text, entry.subtext, self)
            hbox_layout.addWidget(rect_widget)
        self.content_layout.addLayout(hbox_layout)
        self.content_widget.setFixedHeight(self.content_layout.count() * (Gui.WIDGET_HEIGHT + Gui.SPACING))
        self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

    def closeEvent(self, event):
        self.closeCallback()


class Application():
    def __init__(self, argv, handler):
        self.app = QApplication(argv)
        self.window = Gui(handler)

    def start(self):
        self.window.show()
        self.app.exec_()
