import os
import subprocess

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QCursor, QFont
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QSizePolicy

from file_manager.config import settings
from file_manager.ui.widgets.asset_menu import AssetEditMenu


class FileManagerThumbnail(QWidget):
    REF_WIDTH = 150

    deleted = Signal()

    def __init__(self, asset_record, tag_records, path_records, *args, **kwargs):
        """
        :type asset_record: file_manager.data.models.asset.AssetModel
        :type path_records: list[file_manager.data.models.path.PathModel]
        """
        super(FileManagerThumbnail, self).__init__(*args, **kwargs)

        self.asset_record = asset_record
        self.tag_records = tag_records[:]
        self.path_records = path_records[:]

        self._lbl_title = QLabel(asset_record.name)
        self._thumb = QLabel('Placeholder')
        self._lyt_tags = QVBoxLayout()
        self._btn_menu = QPushButton('...')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def update_thumb_size(self):
        size = settings.thumb_size * FileManagerThumbnail.REF_WIDTH / 100.0
        self.setFixedSize(size, size * 1.5)

    def _build_ui(self):
        self.setStyleSheet("QWidget {background-color: rgb(30, 30, 30);}")
        self._lbl_title.setStyleSheet("QLabel {background-color: transparent;}")

        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self._lyt_tags.setContentsMargins(0, 0, 0, 0)
        self._lyt_tags.setSpacing(0)

        for tag_record in self.tag_records:
            lbl = QLabel(tag_record.name)
            lbl.setStyleSheet("QLabel {background-color: %s; color: %s;}" % (tag_record.bg_color, tag_record.fg_color))
            self._lyt_tags.addWidget(lbl)
        self._lyt_tags.addStretch()

        font = QFont('Calibri', 12)
        self._lbl_title.setFixedHeight(28)
        self._lbl_title.setAlignment(Qt.AlignCenter)
        self._lbl_title.setFont(font)

        self._btn_menu.setFixedSize(26, 26)

        def _make_app_button(record):
            btn = QPushButton(record.type)
            btn.setFixedSize(26, 26)
            btn.setToolTip(record.filepath)
            if os.name == 'nt':
                btn.clicked.connect(lambda: subprocess.Popen('explorer /select,"%s"' %
                                                             record.filepath.replace('/', '\\')))
            else:
                btn.clicked.connect(lambda: os.startfile(os.path.dirname(record.filepath)))
            return btn

        _app_icons = QHBoxLayout()
        _app_icons.setAlignment(Qt.AlignLeft)
        _app_icons.setContentsMargins(0, 0, 0, 0)
        _app_icons.setSpacing(0)
        for path_record in self.path_records:
            _app_icons.addWidget(_make_app_button(path_record))

        lyt_bottom = QHBoxLayout()
        lyt_bottom.setContentsMargins(0, 0, 0, 0)
        lyt_bottom.setSpacing(4)
        lyt_bottom.addLayout(_app_icons)
        lyt_bottom.addStretch()
        lyt_bottom.addWidget(self._btn_menu)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(4)
        lyt_main.addWidget(self._lbl_title)
        lyt_main.addWidget(self._thumb)
        lyt_main.addLayout(lyt_bottom)
        lyt_main.addLayout(self._lyt_tags)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_menu.clicked.connect(self._show_menu)

    def _show_menu(self):
        menu = AssetEditMenu([self.asset_record], parent=self)
        menu.assets_deleted.connect(self.deleted.emit)
        menu.exec_(QCursor.pos())

    def _setup_ui(self):
        self.update_thumb_size()
