import os
import re
import subprocess

from PySide2.QtCore import Qt, Signal
from PySide2.QtGui import QCursor, QFont, QPixmap, QIcon
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QInputDialog, QMenu, \
    QApplication

from file_manager.config import settings
from file_manager.data.connection import get_engine
from file_manager.data.query import Query
from file_manager.ui.widgets.asset_menu import AssetEditMenu


class FileManagerThumbnail(QWidget):
    REF_WIDTH = 200
    APP_CACHE = dict()  # dict[type,file_manager.data.models.application.ApplicationModel]

    deleted = Signal()

    @staticmethod
    def cache_app_icons():
        """
        Call before populating thumbnail viewer
        """
        icons_folder = settings.icons_folder()
        if not icons_folder:
            return

        apps = get_engine().select(Query('application'))
        for app in apps:
            if not app.icon:
                continue

            path = os.path.join(icons_folder, app.icon)
            if not os.path.isfile(path):
                continue

            FileManagerThumbnail.APP_CACHE[app.file_type] = QPixmap(path).scaledToHeight(30)

    def __init__(self, asset_record, tag_records, path_records, *args, **kwargs):
        """
        :type asset_record: file_manager.data.models.asset.AssetModel
        :type path_records: list[file_manager.data.models.path.PathModel]
        """
        super(FileManagerThumbnail, self).__init__(*args, **kwargs)

        self.asset_record = asset_record
        self.tag_records = tag_records[:]
        self.path_records = path_records[:]

        self._lbl_title = QLabel(asset_record.name.replace('_', ' '))
        self._thumb = QLabel('Placeholder')
        self._lyt_tags = QVBoxLayout()
        self._btn_menu = QPushButton('...')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def update_thumb_size(self):
        size = settings.thumb_size * FileManagerThumbnail.REF_WIDTH / 100.0
        self.setFixedWidth(size)
        self.setMinimumHeight(size + 50)

        height = (size - 20) / (4.0 / 3)
        self._thumb.setFixedHeight(height)

        lbl = self._thumb.text()
        if 'height=' in lbl:
            self._thumb.setText(re.sub('height=\d+', 'height=%d' % height, lbl))

    def _build_ui(self):
        _app_icons = QHBoxLayout()
        _app_icons.setAlignment(Qt.AlignLeft)
        _app_icons.setContentsMargins(0, 0, 0, 0)
        _app_icons.setSpacing(0)
        for path_record in self.path_records:
            app_pix = FileManagerThumbnail.APP_CACHE.get(path_record.type)
            _app_icons.addWidget(AppButton(path_record, app_pix))

        lyt_bottom = QHBoxLayout()
        lyt_bottom.setContentsMargins(0, 0, 0, 0)
        lyt_bottom.setSpacing(4)
        lyt_bottom.addLayout(_app_icons)
        lyt_bottom.addStretch()
        lyt_bottom.addWidget(self._btn_menu)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(4)
        lyt_main.setAlignment(Qt.AlignTop)
        lyt_main.addWidget(self._lbl_title)
        lyt_main.addWidget(self._thumb)
        lyt_main.addLayout(lyt_bottom)
        lyt_main.addLayout(self._lyt_tags)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_menu.clicked.connect(self._show_menu)

    def _setup_ui(self):
        self.setStyleSheet("QWidget {background-color: rgb(30, 30, 30);}")

        self._lbl_title.setFont(QFont('Calibri', 12))
        self._lbl_title.setFixedHeight(35)
        self._lbl_title.setAlignment(Qt.AlignCenter)
        self._lbl_title.setWordWrap(True)
        self._lbl_title.setStyleSheet(
            """
            background-color: rgba(0, 50, 150, 120);
            color: rgb(225, 225, 225);
            font-family: Consolas;
            font-weight: bold;
            """
        )
        self._lbl_title.mouseDoubleClickEvent = self._edit_title

        self._lyt_tags.setContentsMargins(0, 0, 0, 0)
        self._lyt_tags.setSpacing(0)

        self._btn_menu.setFixedSize(26, 26)

        self._update_tags(refresh=False)
        self._update_thumbnail()

    def _edit_title(self, *args):
        new_text, ok = QInputDialog.getText(self, 'New Title', 'Title:')
        if not ok:
            return

        self.asset_record.name = new_text
        get_engine().update(self.asset_record)
        self._lbl_title.setText(self.asset_record.name)

    def _show_menu(self):
        menu = AssetEditMenu([self.asset_record], parent=self)
        menu.assets_deleted.connect(self.deleted.emit)
        menu.thumbnail_updated.connect(self._update_thumbnail)
        menu.tags_updated.connect(self._update_tags)
        menu.exec_(QCursor.pos())

    def _update_thumbnail(self):
        if not self.asset_record.thumbnail:
            for path in self.path_records:
                if path.type.lower() in ('jpg', 'png'):
                    self._thumb.setText('<img height=%d src="%s"/>' % (self._thumb.height(), path.filepath))
                    self.update_thumb_size()
                    return

        thumbs_folder = settings.thumbs_folder()
        if not thumbs_folder or not self.asset_record.thumbnail:
            return

        thumb_path = os.path.join(thumbs_folder, self.asset_record.thumbnail)
        self._thumb.clear()
        self._thumb.setText('<img height=%d src="%s"/>' % (self._thumb.height(), thumb_path))
        self._thumb.update()
        self.update_thumb_size()

    def _update_tags(self, refresh=True):
        while self._lyt_tags.count():
            wdg = self._lyt_tags.itemAt(0).widget()
            self._lyt_tags.removeWidget(wdg)
            wdg.deleteLater()

        if refresh:
            engine = get_engine()
            links = engine.select(Query('tag_to_asset', asset_id=self.asset_record.id))

            self.tag_records = list()
            if links:
                tag_ids = [_.tag_id for _ in links]
                self.tag_records = engine.select(Query('tag', id=tag_ids))

        for tag_record in self.tag_records:
            lbl = QLabel(tag_record.name)
            lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("QLabel {background-color: %s; color: %s;}" % (tag_record.bg_color, tag_record.fg_color))
            lbl.setFixedHeight(20)

            font = lbl.font()
            font.setPointSize(14)
            lbl.setFont(font)
            self._lyt_tags.addWidget(lbl)


class AppButton(QPushButton):
    def __init__(self, path_record, app_pix):
        """
        :type path_record: file_manager.data.models.path.PathModel
        """
        super(AppButton, self).__init__()

        self.record = path_record

        self.setFixedSize(32, 26)
        self.setToolTip(path_record.filepath)
        self.clicked.connect(self._open_application)

        if app_pix:
            self.setIcon(QIcon(app_pix))
        else:
            self.setText(path_record.type)

    def mouseReleaseEvent(self, event):
        super(AppButton, self).mouseReleaseEvent(event)

        if event.button() == Qt.RightButton:
            menu = QMenu()
            menu.addAction('Copy Path', self._copy_to_clipboard)
            menu.addAction('Open Directory', self._open_directory)
            menu.exec_(QCursor.pos())

    def _find_app(self):
        apps = get_engine().select(Query('application', file_type=self.record.type))
        return apps[0] if apps else None

    def _open_application(self):
        app = self._find_app()
        if app and os.name == 'nt' and app.executable_win:
            exe = app.executable_win
            if os.path.isfile(exe):
                subprocess.Popen([exe.replace('\\', '/'), self.record.filepath.replace('\\', '/')])
                return

        os.startfile(self.record.filepath)

    def _copy_to_clipboard(self):
        cb = QApplication.clipboard()
        cb.setText(self.record.filepath)

    def _open_directory(self):
        if os.name == 'nt':
            subprocess.Popen('explorer /select,"%s"' % self.record.filepath.replace('/', '\\'))
        else:
            os.startfile(os.path.dirname(self.record.filepath))
