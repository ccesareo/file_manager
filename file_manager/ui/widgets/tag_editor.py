from collections import defaultdict

from PySide2.QtWidgets import QDialog, QGridLayout, QComboBox, QVBoxLayout, QLabel, QListWidget

from file_manager.data.connection import get_engine
from file_manager.data.models import TagModel
from file_manager.data.models.tag_to_asset import TagToAssetModel
from file_manager.data.query import Query


class TagEditor(QDialog):
    def __init__(self, asset_records, *args, **kwargs):
        super(TagEditor, self).__init__(*args, **kwargs)

        assert asset_records, 'No Asset records given.'

        self._asset_records = asset_records[:]

        self._shared_tags = self._find_shared_tags(self._asset_records)
        self._all_tags = self._find_all_tags()

        self._cmbo_add_tag = ComboNoScroll()
        self._cmbo_rem_tag = ComboNoScroll()
        self._lyt_shared_tags = QVBoxLayout()

        self._list_history = QListWidget()

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        self.setWindowTitle('Tag Editor')

        lyt_grid = QGridLayout()
        lyt_grid.addWidget(QLabel('Add Tag'), 0, 0)
        lyt_grid.addWidget(self._cmbo_add_tag, 0, 1)
        lyt_grid.addWidget(QLabel('Remove Tag'), 1, 0)
        lyt_grid.addWidget(self._cmbo_rem_tag, 1, 1)

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_grid)
        lyt_main.addWidget(QLabel('History'))
        lyt_main.addWidget(self._list_history)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._cmbo_add_tag.currentIndexChanged.connect(self._add_tag)
        self._cmbo_rem_tag.currentIndexChanged.connect(self._rem_tag)

    def _setup_ui(self):
        self._cmbo_add_tag.setEditable(True)

        count = len(self._asset_records)
        if count == 1:
            self.setWindowTitle('Editing %s' % self._asset_records[0].name)
        else:
            self.setWindowTitle('%d assets' % count)
        self._cmbo_add_tag.addItems([''] + self._all_tags)
        self._cmbo_rem_tag.addItems([''] + self._shared_tags)
        self.resize(400, 300)

    def _add_tag(self):
        tag = self._cmbo_add_tag.currentText()

        if not tag:
            return

        tag_records = get_engine().select(Query('tag', name=tag))[:1]
        if not tag_records:
            new_tag = TagModel(tag, bg_color='#000', fg_color='#fff')
            get_engine().create(new_tag)
            tag_records = [new_tag]

        TagToAssetModel.apply_tags(self._asset_records, tag_records)
        self._list_history.addItem('Tag applied: %s' % tag)
        if tag not in self._shared_tags:
            self._cmbo_rem_tag.addItem(tag)
            self._shared_tags.append(tag)

        self._cmbo_add_tag.setCurrentIndex(0)

    def _rem_tag(self):
        tag = self._cmbo_rem_tag.currentText()

        if not tag:
            return

        tag_records = get_engine().select(Query('tag', name=tag))[:1]

        TagToAssetModel.remove_tags(self._asset_records, tag_records)
        self._list_history.addItem('Tag removed: %s' % tag)

        index = self._cmbo_rem_tag.currentIndex()
        self._cmbo_rem_tag.setCurrentIndex(0)
        self._cmbo_rem_tag.removeItem(index)

    @staticmethod
    def _find_shared_tags(asset_records):
        asset_ids = [x.id for x in asset_records]

        links = get_engine().select(Query('tag_to_asset', asset_id=asset_ids))

        if not links:
            return list()

        links_by_asset = defaultdict(set)
        for link in links:
            links_by_asset[link.asset_id].add(link.tag_id)

        shared_tags = set.intersection(*links_by_asset.values())
        if shared_tags:
            tags = get_engine().select(Query('tag', id=shared_tags))
            names = [x.name for x in tags]
            return sorted(names)

        return list()

    @staticmethod
    def _find_all_tags():
        tags = get_engine().select(Query('tag'))
        names = [x.name for x in tags]
        return sorted(names)


class ComboNoScroll(QComboBox):
    def wheelEvent(self, event):
        event.ignore()
