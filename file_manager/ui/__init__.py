from Qt.QtWidgets import QMainWindow, QVBoxLayout, QWidget

from file_manager.data.connection import get_engine
from ..config import VERSION
from ..data.query import Query
from ..data.entities.tag_to_asset import TagToAssetEntity
from ..ui.menubar import FileManagerMenu
from ..ui.toolbar import FileManagerToolbar
from ..ui.viewer import FileManagerViewer


class FileManagerApp(QMainWindow):
    def __init__(self, *args, **kwargs):
        super(FileManagerApp, self).__init__(*args, **kwargs)

        self._toolbar = FileManagerToolbar(self)
        self._viewer = FileManagerViewer(self)

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def resizeEvent(self, event):
        res = super(FileManagerApp, self).resizeEvent(event)
        self._viewer.update_layout()
        return res

    def _build_ui(self):
        self.setMenuBar(FileManagerMenu())

        lyt_main = QVBoxLayout()
        lyt_main.setSpacing(4)
        lyt_main.addWidget(self._toolbar)
        lyt_main.addWidget(self._viewer)

        wdg = QWidget()
        wdg.setLayout(lyt_main)
        self.setCentralWidget(wdg)

    def _build_connections(self):
        self._toolbar.assets_changed.connect(self._apply_asset_search)
        self._toolbar.tags_changed.connect(self._apply_tag_search)

    def _setup_ui(self):
        self.setWindowTitle('File Manager - %s' % VERSION)

    def _apply_asset_search(self, regex):
        asset_records = list()
        if regex:
            query = Query('asset')
            query.add_filter('name', rvalue='.*%s.*' % regex, operator=Query.OP.MATCH)

            engine = get_engine()
            asset_records = engine.select(query)
        self._viewer.view_assets(asset_records)

    def _apply_tag_search(self, regex):
        asset_records = list()
        if regex:
            query = Query('tag')
            query.add_filter('name', rvalue='.*%s.*' % regex, operator=Query.OP.MATCH)

            engine = get_engine()
            tag_records = engine.select(query)
            asset_records = TagToAssetEntity.find_assets(tag_records)
            """:type: list[file_manager.data.entities.tag.TagEntity]"""
        self._viewer.view_assets(asset_records)
