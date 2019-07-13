from Qt.QtCore import Signal
from Qt.QtWidgets import QMenuBar

from ..data.connection import get_engine
from ..data.entities import TagEntity, AssetEntity
from ..data.entities.application import ApplicationEntity
from ..data.query import Query
from ..ui.importer import AssetImporter
from ..ui.table_editor import TableEditor
from ..ui.widgets.dialogs import ask


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
        editor = TableEditor(TagEntity, allow_create=True, parent=self)
        editor.setWindowTitle('Tag Manager')
        editor.resize(1200, 600)
        editor.exec_()

    def _manage_apps(self):
        editor = TableEditor(ApplicationEntity, allow_create=True, parent=self)
        editor.setWindowTitle('Application Manager')
        editor.resize(1200, 600)
        editor.exec_()

    def _clear_database(self):
        if not ask('Clear Database', 'This is not reversible! Continue?'):
            return

        engine = get_engine()

        AssetEntity.delete(engine.select(Query('asset')))
        engine.delete_many(engine.select(Query('tag')))

        self.database_cleared.emit()

    def _import_assets(self):
        AssetImporter(self).exec_()
