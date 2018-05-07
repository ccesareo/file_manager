from PySide2.QtCore import Signal
from PySide2.QtWidgets import QMenuBar, QMessageBox

from file_manager.data.connection import get_engine
from file_manager.data.models import TagModel, AssetModel
from file_manager.data.models.application import ApplicationModel
from file_manager.data.query import Query
from file_manager.ui.importer import AssetImporter
from file_manager.ui.table_editor import TableEditor


class FileManagerMenu(QMenuBar):
    database_cleared = Signal()

    def __init__(self, *args, **kwargs):
        super(FileManagerMenu, self).__init__(*args, **kwargs)

        self.file_menu = self.addMenu('File')
        self.file_menu.addAction('Import Assets...', self._import_assets)

        self.edit_menu = self.addMenu('Edit')
        self.edit_menu.addAction('Application Manager...', self._manage_apps)
        self.edit_menu.addAction('Tag Manager...', self._manage_tags)

        self.super_menu = self.addMenu('Super User')
        self.super_menu.addAction('Clear Database', self._clear_database)

    def _manage_tags(self):
        editor = TableEditor(TagModel, allow_create=True, parent=self)
        editor.setWindowTitle('Tag Manager')
        editor.resize(1200, 600)
        editor.exec_()

    def _manage_apps(self):
        editor = TableEditor(ApplicationModel, allow_create=True, parent=self)
        editor.setWindowTitle('Application Manager')
        editor.resize(1200, 600)
        editor.exec_()

    def _clear_database(self):
        res = QMessageBox.question(self, 'Clear Database', 'This is not reversible! Continue?',
                                   QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

        if res != QMessageBox.Yes:
            return

        engine = get_engine()

        AssetModel.delete(engine.select(Query('asset')))
        engine.delete_many(engine.select(Query('tag')))

        self.database_cleared.emit()

    def _import_assets(self):
        AssetImporter(self).exec_()
