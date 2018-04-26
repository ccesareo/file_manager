import os
import threading

from PySide2.QtCore import QEvent
from PySide2.QtWidgets import QMessageBox, QDialog, QLineEdit, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, \
    QPushButton, QApplication, QFileDialog

from file_manager.config import LOG
from file_manager.data.connection import get_engine
from file_manager.data.models.asset import AssetModel
from file_manager.data.models.path import PathModel
from file_manager.data.models.tag import TagModel
from file_manager.data.models.tag_to_asset import TagToAssetModel
from file_manager.data.query import Query


class FoundPathEvent(QEvent):
    def __init__(self, count):
        super(FoundPathEvent, self).__init__(QEvent.Type(QEvent.registerEventType()))

        self.count = count


class ResultEvent(QEvent):
    def __init__(self, paths):
        super(ResultEvent, self).__init__(QEvent.Type(QEvent.registerEventType()))

        self.paths = paths


class SearchThread(threading.Thread):
    def __init__(self, wdg, root_path, types_str):
        super(SearchThread, self).__init__()

        self._wdg = wdg
        self._root_path = root_path

        self._extensions = [x.strip() for x in types_str.split(',')] if types_str else list()

        self._cancel = False

    def stop(self):
        self._cancel = True

    def run(self):
        if self._extensions:
            self._extensions = ['.' + x.lstrip('.').lower() for x in self._extensions[:]]

        found = list()
        for root, dir, files in os.walk(self._root_path):
            if self._cancel:
                break
            QApplication.postEvent(self._wdg, FoundPathEvent(len(found)))
            for name in files:
                ext = os.path.splitext(name)[1]
                if self._extensions and ext.lower() not in self._extensions:
                    continue

                found.append(os.path.join(root, name).replace('\\', '/'))
        else:
            QApplication.postEvent(self._wdg, ResultEvent(found))


class AssetImporter(QDialog):
    CACHED_PATH = None

    def __init__(self, *args, **kwargs):
        super(AssetImporter, self).__init__(*args, **kwargs)

        self._lbl_info = QLabel()
        self._thread = None

        self._edit_path = QLineEdit()
        self._btn_browse = QPushButton('...')
        self._edit_types = QLineEdit()

        self._btn_import = QPushButton('Import Assets')
        self._btn_cancel = QPushButton('Cancel')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def event(self, event):
        if isinstance(event, ResultEvent):
            if import_directory_tree(self._edit_path.text().replace('\\', '/'), event.paths):
                self.accept()
            else:
                self._btn_import.setEnabled(True)

        elif isinstance(event, FoundPathEvent):
            self._lbl_info.setText('%d found.' % event.count)
        else:
            return super(AssetImporter, self).event(event)

        return True

    def _build_ui(self):
        lyt_editors = QGridLayout()
        lyt_editors.addWidget(QLabel('Folder Path'), 0, 0)
        lyt_editors.addWidget(self._edit_path, 0, 1)
        lyt_editors.addWidget(self._btn_browse, 0, 2)
        lyt_editors.addWidget(QLabel('File Types'), 1, 0)
        lyt_editors.addWidget(self._edit_types, 1, 1)

        lyt_buttons = QHBoxLayout()
        lyt_buttons.addWidget(self._btn_import)
        lyt_buttons.addWidget(self._btn_cancel)

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_editors)
        lyt_main.addWidget(self._lbl_info)
        lyt_main.addLayout(lyt_buttons)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_import.clicked.connect(self._import_assets)
        self._btn_browse.clicked.connect(self._browse_files)
        self.rejected.connect(self._cancel_thread)

    def _setup_ui(self):
        self.setWindowTitle('Import Assets')
        self._edit_path.setPlaceholderText('Top Level Folder Path')
        self._edit_types.setPlaceholderText('List of types in form of "fbx,mov,jpg"')
        self.setMinimumWidth(600)

        if AssetImporter.CACHED_PATH:
            self._edit_path.setText(AssetImporter.CACHED_PATH)

    def _browse_files(self):
        path = QFileDialog.getExistingDirectory(self, 'Choose Root Folder')
        if not path:
            return
        self._edit_path.setText(path)

    def _cancel_thread(self):
        if self._thread:
            self._thread.stop()
            self._thread.join()

        self._btn_import.setEnabled(True)

    def _import_assets(self):
        self._lbl_info.clear()

        path = self._edit_path.text()

        AssetImporter.CACHED_PATH = path

        if not os.path.isdir(path):
            self._lbl_info.setText('Folder does not exist.')
            return

        if self._thread is not None:
            self._thread.stop()
            self._thread.join()

        self._thread = SearchThread(self, path, self._edit_types.text().strip())
        self._thread.start()

        self._btn_import.setEnabled(False)


def import_directory_tree(root_path, paths):
    engine = get_engine()

    if paths:
        existing_paths = engine.select(Query('path', filepath=paths))
        _paths = [x.filepath for x in existing_paths]
        paths = list(set(paths) - set(_paths))

    types_found = set()
    for item in paths:
        e = os.path.splitext(item)[-1]
        types_found.add(e.strip('.') or 'n/a')

    res = QMessageBox.question(None, 'Found Items',
                               '%d new files found, continue?\n%s' % (len(paths), ','.join(types_found)),
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if res != QMessageBox.Yes:
        return False

    if not paths:
        return False

    # Create assets
    assets = list()
    for path in paths:
        filename = os.path.basename(path)
        asset_name, ext = os.path.splitext(filename)
        assets.append(AssetModel(name=asset_name))
    engine.create_many(assets)

    # Create paths
    _paths = list()
    for asset, path in zip(assets, paths):
        short_path = path.replace(root_path, '').lstrip('/').rsplit('/', 1)[0]
        _paths.append(PathModel(asset.id, path, short_path))
    engine.create_many(_paths)

    # Create tags
    _tags = engine.select(Query('tag', name='new'))
    if not _tags:
        LOG.info('Creating "new" tag.')
        tag = TagModel('new')
        engine.create(tag)
    else:
        tag = _tags[0]

    tags_to_assets = list()
    for asset in assets:
        tags_to_assets.append(TagToAssetModel(asset.id, tag.id))
    engine.create_many(tags_to_assets)

    return True
