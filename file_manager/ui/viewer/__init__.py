from operator import attrgetter

from PySide2.QtCore import Qt
from PySide2.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout

from file_manager.config import settings
from file_manager.data.connection import get_engine
from file_manager.data.query import Query
from file_manager.ui.thumbnail import FileManagerThumbnail
from file_manager.ui.viewer.toolbar import ViewerToolbar
from file_manager.utils import fm_groupby


class FileManagerViewer(QWidget):
    def __init__(self, *args, **kwargs):
        super(FileManagerViewer, self).__init__(*args, **kwargs)

        self._lyt_grid = QGridLayout()
        self._toolbar = ViewerToolbar()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def view_assets(self, asset_names):
        self._clear_grid()

        engine = get_engine()
        asset_records = engine.select(Query('asset', name=asset_names))
        if not asset_records:
            return

        # Find tags
        _links = engine.select(Query('tag_to_asset', asset_id=[_.id for _ in asset_records]))
        links_by_asset = dict(fm_groupby(_links, attrgetter('asset_id')))
        _tags = engine.select(Query('tag', id=[_.tag_id for _ in _links])) if _links else list()
        tags_by_id = {_.id: _ for _ in _tags}

        # Find paths
        _paths = engine.select(Query('path', asset_id=[_.id for _ in asset_records]))
        paths_by_asset = dict(fm_groupby(_paths, attrgetter('asset_id')))

        widgets = list()
        for asset_record in asset_records:
            _links = links_by_asset.get(asset_record.id, list())
            tags = [tags_by_id.get(link.tag_id) for link in _links]

            paths = paths_by_asset.get(asset_record.id, list())

            thumb = FileManagerThumbnail(asset_record, tags, paths)
            thumb.deleted.connect(self._remove_thumb)

            widgets.append(thumb)

        self._layout_widgets(widgets)

    def _build_ui(self):
        self._lyt_grid.setContentsMargins(0, 0, 0, 0)
        self._lyt_grid.setSpacing(10)
        self._lyt_grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)

        scroll_area = QScrollArea()
        scroll_area.setFrameStyle(0)
        scroll_area.setWidget(QWidget())
        scroll_area.widget().setLayout(self._lyt_grid)
        scroll_area.setWidgetResizable(True)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(0)
        lyt_main.addWidget(scroll_area)
        lyt_main.addWidget(self._toolbar)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._toolbar.thumb_size_changed.connect(self._update_layout)

    def _setup_ui(self):
        pass

    def _remove_thumb(self):
        thumb = self.sender()
        self._lyt_grid.removeWidget(thumb)
        thumb.deleteLater()
        self._update_layout()

    def _update_layout(self):
        widgets = list()
        while self._lyt_grid.count():
            wdg = self._lyt_grid.itemAt(0).widget()
            widgets.append(wdg)
            self._lyt_grid.removeWidget(wdg)

        self._layout_widgets(widgets)

    def _layout_widgets(self, widgets):
        for wdg in widgets:
            wdg.update_thumb_size()
        w = self.width()
        items_per_row = int(w / (settings.thumb_size * FileManagerThumbnail.REF_WIDTH / 100.0))
        r, c = 0, 0
        while widgets:
            n = widgets.pop(0)
            self._lyt_grid.addWidget(n, r, c)
            c += 1
            if c >= items_per_row:
                r += 1
                c = 0

    def _clear_grid(self):
        while self._lyt_grid.count():
            item = self._lyt_grid.itemAt(0)
            wdg = item.widget()
            self._lyt_grid.removeWidget(wdg)
            wdg.deleteLater()
