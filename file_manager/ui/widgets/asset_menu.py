import os

from Qt.QtCore import Signal
from Qt.QtWidgets import QMenu, QInputDialog

from ...config import settings
from ...data.entities.asset import AssetEntity
from ...ui.widgets.dialogs import ask
from ...ui.widgets.screen_grabber import grab_screen
from ...ui.widgets.tag_editor import TagEditor


class AssetEditMenu(QMenu):
    assets_deleted = Signal()
    thumbnail_updated = Signal()
    tags_updated = Signal()

    def __init__(self, asset_records, *args, **kwargs):
        """
        :type asset_records: list[file_manager.data.entities.asset.AssetEntity]
        """
        super(AssetEditMenu, self).__init__(*args, **kwargs)

        self._asset_records = asset_records

        self.addAction('Manage Tags', self.add_tag_clicked)
        if len(asset_records) > 1:
            self.addAction('Merge Assets', self.merge_assets_clicked)
        self.addAction('Delete Assets', self.del_assets_clicked)

    def add_tag_clicked(self):
        TagEditor(self._asset_records, parent=self).exec_()
        self.tags_updated.emit()

    def merge_assets_clicked(self):
        new_name, ok = QInputDialog.getText(self, 'New Asset Name', 'Asset Name:', text=self._asset_records[0].name)
        if not ok:
            return

        AssetEntity.merge(self._asset_records, new_name)
        self.assets_deleted.emit()

    def del_assets_clicked(self):
        if not ask('Delete Assets?', 'Are you sure you want to remove these assets?'):
            return

        AssetEntity.delete(self._asset_records)
        self.assets_deleted.emit()
