from PySide2.QtWidgets import QWidget, QGridLayout, QScrollArea, QVBoxLayout

from file_manager.data.connection import get_engine
from file_manager.data.query import Query
from file_manager.ui.thumbnail import FileManagerThumbnail


class FileManagerViewer(QWidget):
    def __init__(self, *args, **kwargs):
        super(FileManagerViewer, self).__init__(*args, **kwargs)

        self._lyt_grid = QGridLayout()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def view_assets(self, asset_names):
        self._clear_grid()

        asset_records = get_engine().select(Query('asset', name=asset_names))

        all_thumbs = list()
        for asset_record in asset_records:
            all_thumbs.append(FileManagerThumbnail(asset_record, list()))

        r, c = 0, 0
        while all_thumbs:
            n = all_thumbs.pop(0)
            self._lyt_grid.addWidget(n, r, c)
            c += 1
            if c >= 5:
                r += 1
                c = 0

    def _build_ui(self):
        self._lyt_grid.setContentsMargins(0, 0, 0, 0)
        self._lyt_grid.setSpacing(10)

    def _build_connections(self):
        pass

    def _setup_ui(self):
        scroll_area = QScrollArea()
        scroll_area.setWidget(QWidget())
        scroll_area.widget().setLayout(self._lyt_grid)
        scroll_area.setWidgetResizable(True)

        lyt_main = QVBoxLayout()
        lyt_main.addWidget(scroll_area)
        self.setLayout(lyt_main)

    def _clear_grid(self):
        while self._lyt_grid.count():
            item = self._lyt_grid.itemAt(0)
            wdg = item.widget()
            self._lyt_grid.removeWidget(wdg)
            wdg.deleteLater()
