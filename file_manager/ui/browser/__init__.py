from collections import defaultdict

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget, QTreeWidget, QVBoxLayout, QTreeWidgetItem

from file_manager.data.connection import get_engine
from file_manager.data.query import Query


class FileManagerBrowser(QWidget):
    assets_selected = Signal(list)

    def __init__(self, *args, **kwargs):
        super(FileManagerBrowser, self).__init__(*args, **kwargs)

        self._tree = QTreeWidget()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self._tree.setHeaderHidden(True)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(0)
        lyt_main.addWidget(self._tree)
        self.setLayout(lyt_main)
        self.setFixedWidth(400)

    def _build_connections(self):
        self._tree.itemSelectionChanged.connect(self._selection_changed)

    def _setup_ui(self):
        self._tree.setSelectionMode(QTreeWidget.ExtendedSelection)

    def apply_tags(self, tag_names):
        self._tree.clear()

        engine = get_engine()

        q = Query('tag')
        q.start_filter_group(q.OP.OR)
        for tag_name in tag_names:
            q.add_filter('name', '^%s$' % tag_name, operator=q.OP.MATCH)
        q.end_filter_group()
        tags = engine.select(q)

        if not tags:
            return

        all_links = engine.select(Query('tag_to_asset', tag_id=[tag.id for tag in tags]))
        links_by_tag = defaultdict(set)
        for link in all_links:
            links_by_tag[link.tag_id].add(link)

        for tag in tags:
            links = links_by_tag[tag.id]
            if not links:
                continue

            assets = engine.select(Query('asset', id=[x.asset_id for x in links]))

            self.add_group([tag], assets)

        self._tree.expandAll()

    def apply_assets(self, asset_names):
        engine = get_engine()

        q = Query('asset')
        q.start_filter_group(q.OP.OR)
        for asset_name in asset_names:
            q.add_filter('name', '^%s$' % asset_name, operator=q.OP.MATCH)
        q.end_filter_group()
        assets = engine.select(q)

        self._tree.clear()
        self.add_group(list(), assets)
        self._tree.expandAll()

    def add_group(self, tags, assets):
        title = ','.join([tag.name for tag in tags]) or 'N/A'

        top_item = QTreeWidgetItem([title])
        self._tree.addTopLevelItem(top_item)

        for asset in assets:
            item = QTreeWidgetItem([asset.name])
            top_item.addChild(item)

    def _selection_changed(self):
        selected_items = self._tree.selectedItems()
        selected_items = [x for x in selected_items if x.parent()]
        asset_names = [x.text(0) for x in selected_items]
        self.assets_selected.emit(asset_names)
