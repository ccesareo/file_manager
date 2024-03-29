from Qt import QtCore, QtGui, QtWidgets

from ... import settings


class ScreenWidget(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super(ScreenWidget, self).__init__(*args, **kwargs)

        self.center_pos = None
        self.start_pos = None
        self.end_pos = None
        self.pixmap = None
        self.current_screen = 99

        self._dt = QtWidgets.QDesktopWidget()

        self._timer_move_screen = QtCore.QTimer()
        self._timer_move_screen.setInterval(150)

        self._timer_draw_screen = QtCore.QTimer()
        self._timer_draw_screen.setInterval(25)

        self._check_mouse_position()
        self._setup_ui()
        self._build_connections()

        self._timer_move_screen.start()
        self.setMouseTracking(True)

    def _setup_ui(self):
        self.setWindowOpacity(.5)
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)

    def _build_connections(self):
        self._timer_move_screen.timeout.connect(self._check_mouse_position)
        self._timer_draw_screen.timeout.connect(self.update)

    def paintEvent(self, event):
        super(ScreenWidget, self).paintEvent(event)

        if not self.center_pos:
            return

        self._build_pos()

        x = self.start_pos.x()
        y = self.start_pos.y()
        w = self.end_pos.x() - x
        h = self.end_pos.y() - y

        rect = QtCore.QRect(x, y, w, h)

        painter = QtGui.QPainter()
        painter.begin(self)
        painter.drawRect(rect)
        painter.end()

    def mousePressEvent(self, event):
        super(ScreenWidget, self).mousePressEvent(event)

        self.center_pos = QtGui.QCursor.pos()
        self._build_pos()
        self._timer_draw_screen.start()

    def mouseReleaseEvent(self, event):
        super(ScreenWidget, self).mouseReleaseEvent(event)

        self._timer_draw_screen.stop()
        self._timer_move_screen.stop()

        self.accept()

    def _build_pos(self):
        if not self.center_pos:
            return

        ratio = 4 / 3.0

        pos = QtGui.QCursor.pos()

        cx = self.center_pos.x()
        cy = self.center_pos.y()
        mx = pos.x()

        xdiff = abs(mx - cx)
        height = (xdiff * 2) / ratio

        x1 = cx - xdiff
        x2 = cx + xdiff
        y1 = cy - (height / 2)
        y2 = cy + (height / 2)

        self.start_pos = QtCore.QPoint(x1, y1)
        self.end_pos = QtCore.QPoint(x2, y2)

    def _check_mouse_position(self):
        _current_screen = self._dt.screenNumber(QtGui.QCursor.pos())
        if _current_screen != self.current_screen:
            geo = self._dt.screenGeometry(_current_screen)
            self.setGeometry(geo)
            self.current_screen = _current_screen


def grab_screen(output_path):
    swdg = ScreenWidget()
    if settings.main_ui:
        settings.main_ui.hide()
    try:
        result = swdg.exec_()
        if not result:
            return False

        rect = QtCore.QRect(swdg.start_pos, swdg.end_pos)
        dw = QtWidgets.QApplication.desktop()
        pix = QtGui.QPixmap.grabWindow(dw.winId(), x=rect.x(), y=rect.y(), w=rect.width(), h=rect.height())

    finally:
        if settings.main_ui:
            settings.main_ui.show()

    return pix.save(output_path, quality=100)
