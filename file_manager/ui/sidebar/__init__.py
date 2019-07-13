from Qt.QtCore import Signal
from Qt.QtWidgets import QTabWidget

from .asset_browser import AssetBrowser


class SideBarBrowser(QTabWidget):
    assets_selected = Signal(list)
    tags_updated = Signal()

    def __init__(self, *args, **kwargs):
        super(SideBarBrowser, self).__init__(*args, **kwargs)

        self._assets = AssetBrowser()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def apply_tags(self, tag_names):
        self._assets.apply_tags(tag_names)

    def apply_assets(self, assets):
        self._assets.apply_assets(assets)

    def _build_ui(self):
        self.addTab(self._assets, 'Assets')

    def _setup_ui(self):
        self.setFixedWidth(400)

    def _build_connections(self):
        self._assets.assets_selected.connect(self.assets_selected.emit)
        self._assets.tags_updated.connect(self.tags_updated.emit)
