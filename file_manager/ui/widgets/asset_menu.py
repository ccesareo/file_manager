import os

from PySide2.QtCore import Signal
from PySide2.QtWidgets import QMenu, QMessageBox, QInputDialog

from file_manager.config import settings
from file_manager.data.connection import get_engine
from file_manager.data.models.asset import AssetModel
from file_manager.ui.widgets.screen_grabber import grab_screen
from file_manager.ui.widgets.tag_editor import TagEditor


class AssetEditMenu(QMenu):
    assets_deleted = Signal()
    thumbnail_updated = Signal()

    def __init__(self, asset_records, *args, **kwargs):
        """
        :type asset_records: list[file_manager.data.models.asset.AssetModel]
        """
        super(AssetEditMenu, self).__init__(*args, **kwargs)

        self._asset_records = asset_records

        self.addAction('Manage Tags', self.add_tag_clicked)
        if len(asset_records) > 1:
            self.addAction('Merge Assets', self.merge_assets_clicked)
        if len(asset_records) == 1:
            self.addAction('Set Thumbnail', self.set_thumbnail)
        self.addAction('Delete Assets', self.del_assets_clicked)

    def add_tag_clicked(self):
        TagEditor(self._asset_records, parent=self).exec_()

    def merge_assets_clicked(self):
        new_name, ok = QInputDialog.getText(None, 'New Asset Name', 'Asset Name:', text=self._asset_records[0].name)
        if not ok:
            return

        AssetModel.merge(self._asset_records, new_name)
        self.assets_deleted.emit()

    def del_assets_clicked(self):
        answer = QMessageBox.question(None, 'Delete Assets?', 'Are you sure you want to remove these assets?',
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return

        self.assets_deleted.emit()
        AssetModel.delete(self._asset_records)

    def set_thumbnail(self):
        asset = self._asset_records[0]

        thumb_path = settings.thumbs_folder()
        filename = '%d.png' % asset.id
        if grab_screen(os.path.join(thumb_path, filename)):
            asset.thumbnail = filename
            get_engine().update(asset)
        self.thumbnail_updated.emit()