import os
import subprocess

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QCursor, QFont, QPixmap
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QSizePolicy, QInputDialog

from file_manager.config import settings
from file_manager.data.connection import get_engine
from file_manager.data.query import Query
from file_manager.ui.widgets.asset_menu import AssetEditMenu


class FileManagerThumbnail(QWidget):
    REF_WIDTH = 200

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

        self._pixmap = None

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def update_thumb_size(self):
        size = settings.thumb_size * FileManagerThumbnail.REF_WIDTH / 100.0
        self.setFixedSize(size, size * 1.5)
        if self._pixmap is not None:
            self._thumb.setPixmap(self._pixmap.scaledToWidth(size, Qt.SmoothTransformation))

    def _build_ui(self):
        self.setStyleSheet("QWidget {background-color: rgb(30, 30, 30);}")
        self._lbl_title.setStyleSheet("QLabel {background-color: transparent;}")

        self._lbl_title.mouseDoubleClickEvent = self._edit_title

        self._thumb.setAlignment(Qt.AlignCenter)
        self._thumb.setSizePolicy(QSizePolicy.MinimumExpanding, QSizePolicy.MinimumExpanding)

        self._lyt_tags.setContentsMargins(0, 0, 0, 0)
        self._lyt_tags.setSpacing(0)

        for tag_record in self.tag_records:
            lbl = QLabel(tag_record.name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("QLabel {background-color: %s; color: %s;}" % (tag_record.bg_color, tag_record.fg_color))
            lbl.setFixedHeight(20)
            self._lyt_tags.addWidget(lbl)
        self._lyt_tags.addStretch()

        font = QFont('Calibri', 8)
        self._lbl_title.setFixedHeight(35)
        self._lbl_title.setAlignment(Qt.AlignCenter)
        self._lbl_title.setFont(font)
        self._lbl_title.setWordWrap(True)

        self._btn_menu.setFixedSize(26, 26)

        def _make_app_button(record):
            btn = QPushButton(record.type)
            btn.setFixedSize(26, 26)
            btn.setToolTip(record.filepath)
            btn.clicked.connect(lambda: self._open_application(record))
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

    def _edit_title(self, *args):
        new_text, ok = QInputDialog.getText(self, 'New Title', 'Title:')
        if not ok:
            return

        self.asset_record.name = new_text
        get_engine().update(self.asset_record)
        self._lbl_title.setText(self.asset_record.name)

    def _open_application(self, record):
        apps = get_engine().select(Query('application', file_type=record.type))
        if apps:
            # TODO - alert if more than 1
            if os.name == 'nt':
                exe = apps[0].executable_win
                subprocess.Popen([exe, record.filepath])
                return

        if os.name == 'nt':
            subprocess.Popen('explorer /select,"%s"' % record.filepath.replace('/', '\\'))
        else:
            os.startfile(os.path.dirname(record.filepath))

    def _show_menu(self):
        menu = AssetEditMenu([self.asset_record], parent=self)
        menu.assets_deleted.connect(self.deleted.emit)
        menu.thumbnail_updated.connect(self._update_thumbnail)
        menu.exec_(QCursor.pos())

    def _setup_ui(self):
        self._update_thumbnail()

    def _update_thumbnail(self):
        if not self.asset_record.thumbnail:
            return

        thumbs_folder = settings.thumbs_folder()
        self._pixmap = QPixmap(os.path.join(thumbs_folder, self.asset_record.thumbnail))
        self.update_thumb_size()
