
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import  QWidget, QHBoxLayout, QVBoxLayout, QApplication, QSizePolicy
from PyQt5.QtGui import QPainter, QPen, QFont, QBrush
from PyQt5.QtCore import QObject, QThread, pyqtSignal, Qt, QRectF
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QScatterSeries, QValueAxis
from PyQt5.QtCore import QPointF
from PyQt5.QtWidgets import QGraphicsSimpleTextItem
from PyQt5.QtGui import QColor, QBrush
import time

from .rectangle import RectangleWidget
from .entry import GuiEntry


class GuiHandler:
    def run(self):
        raise NotImplementedError()


class Worker(QObject):
    finished = pyqtSignal()
    add_inputs = pyqtSignal(list)  # Additional parameter of type string
    add_outputs = pyqtSignal(list)  # Additional parameter of type string
    clear_scroll_and_bottom = pyqtSignal()  # Additional parameter of type string

    def __init__(self, handler):
        super().__init__()
        self.handler = handler

    def run(self):
        while True:
            time.sleep(0.001)
            inputs, outputs, clear, running = self.handler.run()
            if clear:
                self.clear_scroll_and_bottom.emit()
            if inputs:
                self.add_inputs.emit(inputs)
            if outputs:
                self.add_outputs.emit(outputs)
            if not running:
                break

        self.finished.emit()



class PlotWidget(QWidget):
    X_WINDOW = 3000.0

    def __init__(self, parent=None):
        super().__init__(parent)
        self.series = QLineSeries()
        self.markers = QScatterSeries()
        self.markers.setMarkerSize(10)
        self.entries = []

        # Axes
        x_axis = QValueAxis()
        x_axis.setRange(0, PlotWidget.X_WINDOW)
        x_axis.setTickInterval(100.0)
        x_axis.setMinorTickCount(0)
        x_axis.setTickCount(int(PlotWidget.X_WINDOW / 100) + 1)
        x_axis.setLabelsVisible(True)
        x_axis.setLineVisible(False)
        x_axis.setGridLineVisible(True)

        y_axis = QValueAxis()
        y_axis.setRange(-1, 1) 
        y_axis.setVisible(False)

        # Create chart
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 128)))
        self.chart.setBackgroundVisible(True)
        self.chart.addSeries(self.series)
        self.chart.addSeries(self.markers)
        self.chart.setAxisX(x_axis, self.series)
        self.chart.setAxisX(x_axis, self.markers)
        self.chart.setAxisY(y_axis, self.series)
        self.chart.setAxisY(y_axis, self.markers)

        chart_view = QChartView(self.chart)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setFixedHeight(50)
        chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chart_view)

        # Set marker and line color to orange, marker shape to square
        orange = QColor(255, 140, 0)
        self.series.setColor(orange)
        self.markers.setColor(orange)
        self.markers.setMarkerShape(self.markers.MarkerShapeRectangle)
        self.markers.setBrush(QBrush(orange))
        self.markers.setPen(QPen(orange))


    def add(self, entries):
        self.entries.extend(entries)
        self.series.clear()
        self.markers.clear()

        # Remove old marker labels (if any remain)
        for item in self.chart.scene().items():
            if isinstance(item, QGraphicsSimpleTextItem):
                self.chart.scene().removeItem(item)

        plottable = []
        x_time = PlotWidget.X_WINDOW 
        for idx, point in enumerate(reversed(self.entries)):
            if x_time <= 0:
                length = len(self.entries)
                self.entries = self.entries[length-idx:length]
                break

            delay, text = point.get_delay(), point.get_text()
            plottable.append((x_time, 0, text))
            x_time -= delay

        for x, y, l in plottable:
            self.series.append(x, y)
            self.markers.append(x, y)

            item = QGraphicsSimpleTextItem(l)
            item.setBrush(Qt.red)
            item.setFont(QFont('Arial', 8))

            item.setPos(self.chart.mapToPosition(QPointF(x, y - 1)))
            self.chart.scene().addItem(item)


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

    def add(self, specials):
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        for entry in specials:
            layout.addWidget(RectangleWidget(entry.get_text(), entry.get_subtext(), self, is_red=True))
        self.layout.addLayout(layout)

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
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

    def add(self, entries):
        for entry in entries:
            self.layout.addWidget(RectangleWidget(entry.get_text(), entry.get_subtext(), self))

        count = self.layout.count()
        if count > Gui.MAX_WIDGET_COUNT:
            for i in range(count - Gui.MAX_WIDGET_COUNT):
                if item := self.layout.takeAt(0):
                    if widget:= item.widget():
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
        self._set_size()

        self.main = QVBoxLayout(self)
        self.main.setSpacing(Gui.SPACING)
        self.main.setContentsMargins(Gui.SPACING, Gui.SPACING, Gui.SPACING, Gui.SPACING)

        self.content = ContentPanel(self)
        self.main.addWidget(self.content)

        self.plot = PlotWidget(self)
        self.main.addWidget(self.plot)

        self.bottom = BottomPanel(self)
        self.main.addWidget(self.bottom)

        self.thread = QThread()
        self.worker = Worker(handler)
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.add_inputs.connect(self.add_inputs)
        self.worker.add_outputs.connect(self.add_outputs)
        self.worker.clear_scroll_and_bottom.connect(self.clear_scroll_and_bottom)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.thread.start()

    def _set_size(self):
        sg = QApplication.screens()[0].geometry()
        x = sg.x()
        y = sg.y()
        self.setGeometry(x, y + 100, sg.width(), 900)

    def add_inputs(self, entries):
        self.plot.add(entries)
        self.bottom.add(entries)

    def add_outputs(self, entries):
        self.content.add(entries)

    def _clear_layout(self, layout):
        if layout is not None:
            while layout.count():
                item = layout.takeAt(0)
                if widget := item.widget():
                    widget.deleteLater()
                else:
                    self._clear_layout(item.layout())

    def clear_scroll_and_bottom(self):
        self._clear_layout(self.content.layout)
        self._clear_layout(self.bottom.layout)


        
class GuiApplication():
    def __init__(self, argv, handler):
        self.app = QApplication(argv)
        self.gui = Gui(handler)

    def start(self):
        self.gui.show()
        self.app.exec_()