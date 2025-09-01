from PyQt5.QtWidgets import QWidget, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QDateTime
from PyQt5.QtWidgets import QHBoxLayout
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QApplication, QSizePolicy
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
    X_OFFSET = -10

    def __init__(self, parent=None, colors=None):
        super().__init__(parent)
        self.entries = []
        self.markers = {}
        self.series = QLineSeries()
        pen = QPen()
        pen.setWidth(1)
        self.series.setPen(pen)
        self.series.setColor(QColor(255, 140, 0))
        for _color in colors:
            s = QScatterSeries()
            color = QColor(_color)
            s.setMarkerSize(8)
            s.setMarkerShape(QScatterSeries.MarkerShapeRectangle)
            s.setColor(color)
            s.setBrush(QBrush(color))
            s.setPen(QPen(color))
            self.markers[_color] = s

        # Axes
        x_axis = QValueAxis()
        x_axis.setRange(0, PlotWidget.X_WINDOW)
        x_axis.setTickInterval(100.0)
        x_axis.setMinorTickCount(0)
        x_axis.setTickCount(int(PlotWidget.X_WINDOW / 100) + 1)
        x_axis.setLabelsVisible(False)
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

        for s in self.markers.values():
            self.chart.addSeries(s)
        self.chart.setAxisX(x_axis, self.series)

        for s in self.markers.values():
            self.chart.setAxisX(x_axis, s)
        self.chart.setAxisY(y_axis, self.series)

        for s in self.markers.values():
            self.chart.setAxisY(y_axis, s)

        chart_view = QChartView(self.chart)
        chart_view.setStyleSheet("background: transparent;")
        chart_view.setFixedHeight(50)
        chart_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(chart_view)

    def add(self, entries):
        self.entries.extend(entries)
        self.series.clear()

        # Clear all marker series
        for s in self.markers.values():
            s.clear()

        # Remove old marker labels (if any remain)
        for item in self.chart.scene().items():
            if isinstance(item, QGraphicsSimpleTextItem):
                self.chart.scene().removeItem(item)

        points = []
        x_time = PlotWidget.X_WINDOW - PlotWidget.X_OFFSET
        for entry in reversed(self.entries):
            if x_time <= 0:
                break
            points.append((x_time, entry.get_color(), entry.get_text()))
            x_time -= entry.get_delay()
        self.entries = self.entries[-len(points):]

        x_previous = None
        label_below = True  # Start with label below
        for x, color, text in points:
            self.series.append(x + PlotWidget.X_OFFSET, 0)
            self.markers[color].append(x + PlotWidget.X_OFFSET, 0)

            label = QGraphicsSimpleTextItem(text)
            label.setBrush(Qt.white)
            label.setFont(QFont("Arial", 8))

            # Position the label, alternating if too close to the previous one
            if x_previous is not None and abs(x - x_previous) < 20:
                y_offset = 5 if label_below else -3
                label_below = not label_below
            else:
                y_offset = -3
                label_below = True

            label.setPos(
                self.chart.mapToPosition(QPointF(x + PlotWidget.X_OFFSET, y_offset))
            )
            self.chart.scene().addItem(label)
            x_previous = x


class ContentPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setSpacing(Gui.SPACING)
        self.layout.setContentsMargins(Gui.SPACING, Gui.SPACING, Gui.SPACING, Gui.SPACING)
        self.setLayout(self.layout)
        self.max_rows = 10

    def add(self, specials):
        self.last_add_time = QDateTime.currentDateTime()
        layout = QHBoxLayout()
        layout.setAlignment(Qt.AlignLeft)
        for entry in specials:
            widget = RectangleWidget(entry.get_text(), entry.get_subtext(), self, is_red=True)
            layout.addWidget(widget)
        self.layout.addLayout(layout)

        while self.layout.count() > self.max_rows:
            self.remove_row(0)

    def fade_and_remove_row(self, index):
        item = self.layout.itemAt(index)
        if item:
            row_layout = item.layout()
            if row_layout:
                for i in range(row_layout.count()):
                    widget = row_layout.itemAt(i).widget()
                    if widget:
                        effect = QGraphicsOpacityEffect(widget)
                        widget.setGraphicsEffect(effect)
                        animation = QPropertyAnimation(effect, b"opacity")
                        animation.setDuration(1000)
                        animation.setStartValue(1)
                        animation.setEndValue(0)
                        animation.setEasingCurve(QEasingCurve.OutQuad)
                        animation.finished.connect(widget.deleteLater)
                        animation.start()
                self.layout.takeAt(index)

    def remove_row(self, index):
        item = self.layout.takeAt(index)
        if item:
            row_layout = item.layout()
            if row_layout:
                while row_layout.count():
                    witem = row_layout.takeAt(0)
                    widget = witem.widget()
                    if widget:
                        widget.deleteLater()


class BottomPanel(QWidget):
    def __init__(self, parent, content_panel):
        super().__init__(parent)
        self.content_panel = content_panel
        self.layout = QHBoxLayout(self)
        self.layout.setAlignment(Qt.AlignLeft)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)

        self.last_add_time = QDateTime.currentDateTime()
        self.inactivity_timer = QTimer(self)
        self.inactivity_timer.timeout.connect(self.check_inactivity)
        self.inactivity_timer.start(1000)  # Check every second

    def add(self, entries):
        self.last_add_time = QDateTime.currentDateTime()
        for entry in entries:
            widget = RectangleWidget(entry.get_text(), entry.get_subtext(), self)
            self.layout.addWidget(widget)

        count = self.layout.count()
        if count > Gui.MAX_WIDGET_COUNT:
            for i in range(count - Gui.MAX_WIDGET_COUNT):
                self.remove_widget(0)

    def check_inactivity(self):
        if self.last_add_time.msecsTo(QDateTime.currentDateTime()) > 3000:
            if self.layout.count() > 0:
                self.fade_and_remove_widget(0)
                self.content_panel.fade_and_remove_row(0)

    def fade_and_remove_widget(self, index):
        item = self.layout.itemAt(index)
        if item:
            widget = item.widget()
            if widget:
                effect = QGraphicsOpacityEffect(widget)
                widget.setGraphicsEffect(effect)
                animation = QPropertyAnimation(effect, b"opacity")
                animation.setDuration(1000)
                animation.setStartValue(1)
                animation.setEndValue(0)
                animation.setEasingCurve(QEasingCurve.OutQuad)
                animation.finished.connect(widget.deleteLater)
                animation.start()
                self.layout.takeAt(index)

    def remove_widget(self, index):
        item = self.layout.takeAt(index)
        if item:
            widget = item.widget()
            if widget:
                widget.deleteLater()


# --- Main Gui class ---
class Gui(QWidget):
    SPACING = 0
    MAX_WIDGET_COUNT = 15

    def __init__(self, handler, colors):
        super().__init__()
        self.setWindowTitle("Inputs")
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlag(Qt.WindowTransparentForInput, True)
        self.setStyleSheet("color: red; background-color: transparent;")
        self.setWindowOpacity(0.8)
        self._set_size()

        self.main = QVBoxLayout(self)
        self.main.setSpacing(Gui.SPACING)
        self.main.setContentsMargins(Gui.SPACING, Gui.SPACING, Gui.SPACING, Gui.SPACING)

        self.content = ContentPanel(self)
        self.main.addWidget(self.content, 8)

        self.bottom = BottomPanel(self, self.content)
        self.main.addWidget(self.bottom, 1)

        self.plot = PlotWidget(self, colors)
        self.main.addWidget(self.plot, 1)

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
        x, y = sg.x(),  sg.y()
        width, height = sg.width(), sg.height()
        print(x, y, width, height)
        self.setGeometry(x, y, width, height)

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


class GuiApplication:
    def __init__(self, argv, handler, colors):
        self.app = QApplication(argv)
        self.gui = Gui(handler, colors)

    def start(self):
        self.gui.show()
        self.app.exec_()
