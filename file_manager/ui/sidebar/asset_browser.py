from collections import defaultdict
from operator import attrgetter

from Qt.QtCore import Signal, QTimer, Qt
from Qt.QtGui import QCursor
from Qt.QtWidgets import QWidget, QTreeWidget, QVBoxLayout, QTreeWidgetItem

from ..widgets.asset_menu import AssetEditMenu
from ...data.connection import get_engine
from ...data.query import Query


class AssetBrowser(QWidget):
    assets_selected = Signal(list)
    tags_updated = Signal()

    def __init__(self, *args, **kwargs):
        super(AssetBrowser, self).__init__(*args, **kwargs)

        self._tree = QTreeWidget()
        self._timer_selection = QTimer()
        self._timer_selection.setInterval(300)
        self._timer_selection.setSingleShot(True)

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def apply_tags(self, tag_names):
        self._tree.clear()
        if not tag_names:
            return

        engine = get_engine()

        q = Query('tag')
        q.start_filter_group(q.OP.OR)
        for tag_name in tag_names:
            q.add_filter('name', '^%s$' % tag_name, operator=q.OP.MATCH)
        q.end_filter_group()
        q.add_order_by('name', q.ORDER.ASC)
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
            assets.sort(key=attrgetter('name'))

            self.add_group([tag], assets)

        self._tree.expandAll()

    def apply_assets(self, asset_names):
        self._tree.clear()

        if not asset_names:
            return

        engine = get_engine()

        q = Query('asset')
        q.start_filter_group(q.OP.OR)
        for asset_name in asset_names:
            q.add_filter('name', '^%s$' % asset_name, operator=q.OP.MATCH)
        q.end_filter_group()
        q.add_order_by('name', q.ORDER.ASC)
        assets = engine.select(q)

        self.add_group(list(), assets)
        self._tree.expandAll()

    def add_group(self, tags, assets):
        title = ','.join([tag.name for tag in tags]) or 'N/A'

        top_item = QTreeWidgetItem([title])
        self._tree.addTopLevelItem(top_item)

        for asset in assets:
            item = QTreeWidgetItem([asset.name])
            top_item.addChild(item)

    def clear(self):
        self._tree.clear()

    def _build_ui(self):
        self._tree.setHeaderHidden(True)

        lyt_main = QVBoxLayout()
        lyt_main.setContentsMargins(0, 0, 0, 0)
        lyt_main.setSpacing(0)
        lyt_main.addWidget(self._tree)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._tree.itemSelectionChanged.connect(self._timer_selection.start)
        self._timer_selection.timeout.connect(self._selection_changed)
        self._tree.customContextMenuRequested.connect(self._context_menu)

    def _setup_ui(self):
        self._tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self._tree.setContextMenuPolicy(Qt.CustomContextMenu)

    def _context_menu(self):
        selected_items = self._tree.selectedItems()
        selected_items = [x for x in selected_items if x.parent()]
        asset_names = [x.text(0) for x in selected_items]
        if not asset_names:
            return

        assets = get_engine().select(Query('asset', name=asset_names))
        # TODO - catch emit if assets were removed
        menu = AssetEditMenu(assets, parent=self)
        menu.assets_deleted.connect(self._remove_selected)
        menu.tags_updated.connect(self.tags_updated.emit)
        menu.exec_(QCursor.pos())

    def _remove_selected(self):
        selected_items = self._tree.selectedItems()
        for item in selected_items:
            p = item.parent()
            p.removeChild(item)

    def _selection_changed(self):
        selected_items = self._tree.selectedItems()
        selected_items = [x for x in selected_items if x.parent()]
        asset_names = [x.text(0) for x in selected_items]
        self.assets_selected.emit(asset_names)
