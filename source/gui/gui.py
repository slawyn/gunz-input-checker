
from PyQt5.QtWidgets import QHBoxLayout, QPushButton
from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QScrollArea, QApplication
from PyQt5.QtGui import QPainter, QPen, QFont, QBrush
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QRectF
from PyQt5.QtChart import QChart, QChartView, QLineSeries
from PyQt5.QtChart import QScatterSeries
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from PyQt5.QtGui import QColor, QBrush


import time

from .rectangle import RectangleWidget


class GuiHandler:
    def run(self):
        raise NotImplementedError()

    def is_running(self):
        raise NotImplementedError()

class Worker(QObject):
    finished = pyqtSignal()
    add_rectangle = pyqtSignal(list, list)  # Additional parameter of type string
    clear_scroll_and_bottom = pyqtSignal()  # Additional parameter of type string

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def run(self):
        while self.handler.is_running():
            time.sleep(0.001)
            entries, clear = self.handler.run()
            if clear:
                self.clear_scroll_and_bottom.emit()
            if entries:
                self.add_rectangle.emit(entries.normals, entries.specials)

        self.finished.emit()



class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.series = QLineSeries()
        self.marker_series = QScatterSeries()
        self.marker_series.setMarkerSize(10)
        self.plot_points = []  # List of (timestamp, value, label)
        self.plot_span = 3.0  # seconds
        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.marker_series)
        self.chart.createDefaultAxes()
        self.chart.legend().hide()
        # Hide y-axis
        y_axis = self.chart.axisY()
        if y_axis:
            y_axis.setVisible(False)
        # Hide x-axis line, but keep ticks for time
        x_axis = self.chart.axisX()
        if x_axis:
            x_axis.setLineVisible(False)
            x_axis.setGridLineVisible(False)
            x_axis.setRange(0, self.plot_span)
        self.x_axis = x_axis
        self.chart_view = QChartView(self.chart)
        self.chart_view.setStyleSheet("background: transparent;")
        self.chart_view.setFixedHeight(40)
        self.chart_view.setSizePolicy(self.chart_view.sizePolicy().Expanding, self.chart_view.sizePolicy().Fixed)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.chart_view)
        bg_color = QColor(0, 0, 0)
        bg_color.setAlphaF(0.5)
        self.chart.setBackgroundBrush(QBrush(bg_color))
        self.chart.setBackgroundVisible(True)

    def add_point(self, label):
        now = time.time()
        self.plot_points.append((now, 0, label))
        min_time = now - self.plot_span
        self.plot_points = [(t, v, l) for t, v, l in self.plot_points if t >= min_time]
        self.series.clear()
        self.marker_series.clear()
        for t, v, l in self.plot_points:
            x = t - min_time
            self.series.append(x, v)
            self.marker_series.append(x, v)
        # Remove old marker labels
        for item in self.chart.scene().items():
            if hasattr(item, '_is_marker_label'):
                self.chart.scene().removeItem(item)
        for t, v, l in self.plot_points:
            x = t - min_time
            if l:
                label_item = QGraphicsSimpleTextItem(l)
                label_item.setBrush(Qt.red)
                label_item.setFont(QFont('Arial', 8))
                pos = self.chart.mapToPosition(QPointF(x, v))
                label_item.setPos(pos)
                label_item._is_marker_label = True
                self.chart.scene().addItem(label_item)
        if self.x_axis:
            self.x_axis.setRange(0, self.plot_span)

# --- ContentPanel ---
class ContentPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(Gui.SPACING)
        self.layout.setContentsMargins(Gui.SPACING, Gui.SPACING, Gui.SPACING, Gui.SPACING)
        self.setLayout(self.layout)
        self.max_rows = 10  # Maximum number of rows to show
        self.setMaximumHeight(self.max_rows * (RectangleWidget.RECT_SIZE + Gui.SPACING))

    def add_specials(self, specials):
        hbox_layout = QHBoxLayout()
        hbox_layout.setAlignment(Qt.AlignLeft)
        for entry in specials:
            hbox_layout.addWidget(RectangleWidget(entry.text, entry.subtext, self, is_red=True))
        self.layout.addLayout(hbox_layout)
        # Remove oldest rows if exceeding max_rows
        while self.layout.count() > self.max_rows:
            item = self.layout.takeAt(0)
            if item:
                # Remove all widgets in the row
                row_layout = item.layout()
                if row_layout:
                    while row_layout.count():
                        witem = row_layout.takeAt(0)
                        widget = witem.widget()
                        if widget:
                            widget.deleteLater()
                del row_layout
        # Set fixed height to max_rows worth of rectangles
        self.setFixedHeight(self.max_rows * (RectangleWidget.RECT_SIZE + Gui.SPACING))

# --- BottomPanel ---
class BottomPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignLeft)
        self.layout.setSpacing(10)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
    def add_normals(self, normals):
        for entry in normals:
            self.layout.addWidget(RectangleWidget(entry.text, entry.subtext, self))
        widget_count = self.layout.count()
        if widget_count > Gui.MAX_WIDGET_COUNT:
            for i in range(widget_count - Gui.MAX_WIDGET_COUNT):
                if item := self.layout.takeAt(0):
                    widget = item.widget()
                    if widget:
                        widget.deleteLater()

# --- Main Gui class ---
class Gui(QWidget):
    SPACING = 0
    MAX_WIDGET_COUNT = 15

    def __init__(self, handler):
        super().__init__()
        self.setWindowTitle("Inputs")
        self.setWindowFlags(
            Qt.FramelessWindowHint |
            Qt.WindowStaysOnTopHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)
        self.setStyleSheet("color: red; background-color: transparent;")
        self.setWindowOpacity(0.8)
        self.set_position_to_left_screen()
        self.closeCallback = handler.stop
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(Gui.SPACING)
        self.main_layout.setContentsMargins(Gui.SPACING, Gui.SPACING, Gui.SPACING, Gui.SPACING)
        self.content_panel = ContentPanel(self)
        self.main_layout.addWidget(self.content_panel)
        self.plot_widget = PlotWidget(self)
        self.main_layout.addWidget(self.plot_widget)
        self.bottom_panel = BottomPanel(self)
        self.main_layout.addWidget(self.bottom_panel)
        self.thread = QThread()
        self.worker = Worker(handler)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.add_rectangle.connect(self.add_rectangle)
        self.worker.clear_scroll_and_bottom.connect(self.clear_scroll_and_bottom)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def set_position_to_left_screen(self):
        screen_geometry = QApplication.screens()[0].geometry()
        x = screen_geometry.x()
        y = screen_geometry.y()
        self.setGeometry(x, y + 100, 900, 900)

    def add_rectangle(self, normals, specials):
        label = None
        if specials and len(specials) > 0:
            label = specials[0].text
        elif normals and len(normals) > 0:
            label = normals[0].text
            self.plot_widget.add_point(label)
        else:
            label = ""

        if specials:
            self.content_panel.add_specials(specials)
        if normals:
            self.bottom_panel.add_normals(normals)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if widget := item.widget():
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def clear_scroll_and_bottom(self):
        self._clear_layout(self.content_panel.layout)
        self._clear_layout(self.bottom_panel.layout)

    def closeEvent(self, event):
        self.closeCallback()

        
class GuiApplication():
    def __init__(self, argv, handler):
        self.app = QApplication(argv)
        self.gui = Gui(handler)

    def start(self):
        self.gui.show()
        self.app.exec_()