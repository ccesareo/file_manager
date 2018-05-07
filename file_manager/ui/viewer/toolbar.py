from PySide2.QtCore import Qt, Signal
from PySide2.QtWidgets import QWidget, QSlider, QHBoxLayout, QLabel

from file_manager.config import settings


class ViewerToolbar(QWidget):
    thumb_size_changed = Signal()

    def __init__(self, *args, **kwargs):
        super(ViewerToolbar, self).__init__(*args, **kwargs)

        self._thumb_size = QSlider()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self._thumb_size.setRange(100, 400)
        self._thumb_size.setValue(settings.thumb_size)
        self._thumb_size.setOrientation(Qt.Horizontal)
        self._thumb_size.setFixedWidth(300)

        lyt_main = QHBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(0)
        lyt_main.addStretch()
        lyt_main.addWidget(QLabel('%d %%' % self._thumb_size.minimum()))
        lyt_main.addSpacing(5)
        lyt_main.addWidget(self._thumb_size)
        lyt_main.addSpacing(5)
        lyt_main.addWidget(QLabel('%d %%' % self._thumb_size.maximum()))
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._thumb_size.valueChanged.connect(self._thumb_size_changed)

    def _setup_ui(self):
        pass

    def _thumb_size_changed(self):
        settings.thumb_size = self._thumb_size.value()
        self.thumb_size_changed.emit()
