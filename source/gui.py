from PyQt5.QtWidgets import QHBoxLayout, QPushButton
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
    def __init__(self):
        self.normals = []
        self.specials = []

    def add_normal(self, text, subtext):
        self.normals.append(Entry(text, subtext))

    def add_special(self, text, subtext):
        self.specials.append(Entry(text, subtext))

    def __str__(self):
        return f"{self.name}: {[str(entry) for entry in self.normals]}"


class Worker(QObject):
    finished = pyqtSignal()
    add_rectangle = pyqtSignal(list, list)  # Additional parameter of type string

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def run(self):
        while self.handler.is_running():
            time.sleep(0.001)
            if entries := self.handler.run():
                self.add_rectangle.emit(entries.normals, entries.specials)

        self.finished.emit()


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
            painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))  # Fill with red
            painter.setPen(QPen(Qt.red, 2, Qt.SolidLine))
        else:
            painter.setBrush(Qt.NoBrush)  # No fill for non-red rectangles
            painter.setPen(QPen(Qt.black, 2, Qt.SolidLine))

        rect = QRectF(10, 10, self.width() - 20, self.height() - 20)
        painter.drawRect(rect)

        font = QFont()
        font.setPointSize(8)
        painter.setPen(QPen(Qt.blue))
        painter.setFont(font)

        text_rect = QRectF(10, 10, self.width() - 20, (self.height() - 20) / 2)
        subtext_rect = QRectF(10, 30, self.width() - 20, (self.height() - 20) / 2)

        painter.drawText(text_rect, Qt.AlignCenter, self.text)
        painter.drawText(subtext_rect, Qt.AlignCenter, self.subtext)


class Gui(QMainWindow):
    SPACING = 0
    MAX_WIDGET_COUNT = 15

    def __init__(self, handler):
        super().__init__()
        self.setWindowTitle("Inputs")

        # Remove the window frame
        # self.setWindowFlags(Qt.FramelessWindowHint)

        # Make the background transparent
        self.setAttribute(Qt.WA_TranslucentBackground)
        # self.setStyleSheet("background:transparent;")
        self.setWindowOpacity(0.8)
        self.setGeometry(100, 100, 1000, 1000)
        self.set_position_to_left_screen()

        self.closeCallback = handler.stop

        # Main layout combining scroll area and bottom pane
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(Gui.SPACING)
        main_layout.setContentsMargins(5, 5, 5, Gui.SPACING)

        # Scrollable content pane
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(Gui.SPACING)
        self.content_layout.setContentsMargins(5, 5, 5, Gui.SPACING)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setWidget(self.content_widget)

        # Add scroll area to the main layout
        main_layout.addWidget(self.scroll_area)

        # Bottom pane with a horizontal layout
        self.bottom_pane = QWidget()
        self.bottom_pane.setStyleSheet("background-color: lightblue;")
        self.bottom_layout = QHBoxLayout(self.bottom_pane)
        self.bottom_layout.setAlignment(Qt.AlignLeft)
        self.bottom_layout.setSpacing(10)
        self.bottom_layout.setContentsMargins(0, 0, 0, 0)

        # Add the bottom pane to the main layout
        main_layout.addWidget(self.bottom_pane)

        # Set the main widget as the central widget
        self.setCentralWidget(main_widget)

        # Worker and threading setup
        self.thread = QThread()
        self.worker = Worker(handler)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.add_rectangle.connect(self.add_rectangle)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)

        self.thread.start()

    def set_position_to_left_screen(self):
        # Get the screen geometry for the primary screen (or first screen)
        screen_geometry = QApplication.screens()[0].geometry()

        # Set the window's position to the left screen
        x = screen_geometry.x()  # Left screen's x-coordinate
        y = screen_geometry.y()  # Top of the screen
        self.setGeometry(x, y, 900, 600)  # Adjust width and height as needed

    def add_rectangle(self, normals, specials):
        if specials:
            hbox_layout = QHBoxLayout()
            hbox_layout.setAlignment(Qt.AlignLeft)

            # Add red rectangle
            for entry in specials:
                hbox_layout.addWidget(RectangleWidget(entry.text, entry.subtext, self, is_red=True))

            # Add horizontal layout to the main vertical layout
            self.content_layout.addLayout(hbox_layout)

            widget_count = self.content_layout.count()
            if widget_count > Gui.MAX_WIDGET_COUNT:
                for i in range(widget_count - Gui.MAX_WIDGET_COUNT):
                    # Take the first widget (index 0), remove it from the layout, and delete it
                    if item := self.content_layout.takeAt(0):
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()

            # Dynamically adjust the content widget height
            total_height = self.content_layout.count() * (RectangleWidget.RECT_SIZE + Gui.SPACING)  # Adjust widget height as necessary
            self.content_widget.setFixedHeight(total_height)
            self.scroll_area.verticalScrollBar().setValue(self.scroll_area.verticalScrollBar().maximum())

        if normals:
            # Add normal rectangle
            for entry in normals:
                self.bottom_layout.addWidget(RectangleWidget(entry.text, entry.subtext, self))

            widget_count = self.bottom_layout.count()
            if widget_count > Gui.MAX_WIDGET_COUNT:
                for i in range(widget_count - Gui.MAX_WIDGET_COUNT):
                    # Take the first widget (index 0), remove it from the layout, and delete it
                    if item := self.bottom_layout.takeAt(0):
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()

    def closeEvent(self, event):
        self.closeCallback()


class Application():
    def __init__(self, argv, handler):
        self.app = QApplication(argv)
        self.window = Gui(handler)

    def start(self):
        self.window.show()
        self.app.exec_()
