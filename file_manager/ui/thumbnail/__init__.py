from PySide2.QtCore import Qt
from PySide2.QtGui import QCursor
from PySide2.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QMenu

from file_manager.ui.widgets.tag_editor import TagEditor


class FileManagerThumbnail(QWidget):
    def __init__(self, asset_record, path_records, *args, **kwargs):
        """
        :type asset_record: file_manager.data.models.asset.AssetModel
        :type path_records: list[file_manager.data.models.path.PathModel]
        """
        super(FileManagerThumbnail, self).__init__(*args, **kwargs)

        self.asset_record = asset_record
        self.path_records = path_records[:]

        self._lbl_title = QLabel(asset_record.name)
        self._thumb = QLabel('Placeholder')
        self._btn_menu = QPushButton('...')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self.setStyleSheet("""QWidget {background-color: rgb(30, 30, 30);}""")
        self._thumb.setAlignment(Qt.AlignCenter)
        self._lbl_title.setFixedHeight(32)

        self._btn_menu.setFixedSize(32, 32)

        def _make_test_button(t):
            btn = QPushButton(t)
            btn.setFixedSize(32, 32)
            return btn

        _app_icons = QHBoxLayout()
        _app_icons.setAlignment(Qt.AlignLeft)
        _app_icons.setContentsMargins(0, 0, 0, 0)
        _app_icons.setSpacing(0)
        for path_record in self.path_records:
            _app_icons.addWidget(_make_test_button(path_record.type))

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
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_menu.clicked.connect(self._show_menu)

    def _show_menu(self):
        menu = ThumbnailMenu(self)
        a = menu.exec_(QCursor.pos())
        if a is None:
            return

    def _setup_ui(self):
        self.setFixedHeight(250)


class ThumbnailMenu(QMenu):
    def __init__(self, thumb, *args, **kwargs):
        """
        :type thumb: FileManagerThumbnail
        """
        super(ThumbnailMenu, self).__init__(thumb, *args, **kwargs)

        self.thumb = thumb

        self.addAction('Manage Tags', self.add_tag_clicked)

    def add_tag_clicked(self):
        TagEditor([self.thumb.asset_record], parent=self).exec_()
