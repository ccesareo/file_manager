import os

from PySide2.QtWidgets import QMessageBox, QDialog, QLineEdit, QGridLayout, QLabel, QVBoxLayout, QHBoxLayout, \
    QPushButton

from file_manager.config import LOG
from file_manager.data.connection import get_engine
from file_manager.data.models.asset import AssetModel
from file_manager.data.models.path import PathModel
from file_manager.data.models.tag import TagModel
from file_manager.data.models.tag_to_asset import TagToAssetModel
from file_manager.data.query import Query


class AssetImporter(QDialog):
    def __init__(self, *args, **kwargs):
        super(AssetImporter, self).__init__(*args, **kwargs)

        self._lbl_errors = QLabel()

        self._edit_path = QLineEdit()
        self._edit_types = QLineEdit()

        self._btn_import = QPushButton('Import Assets')
        self._btn_cancel = QPushButton('Cancel')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def _build_ui(self):
        lyt_editors = QGridLayout()
        lyt_editors.addWidget(QLabel('Folder Path'), 0, 0)
        lyt_editors.addWidget(self._edit_path, 0, 1)
        lyt_editors.addWidget(QLabel('File Types'), 1, 0)
        lyt_editors.addWidget(self._edit_types, 1, 1)

        lyt_buttons = QHBoxLayout()
        lyt_buttons.addWidget(self._btn_import)
        lyt_buttons.addWidget(self._btn_cancel)

        lyt_main = QVBoxLayout()
        lyt_main.addLayout(lyt_editors)
        lyt_main.addWidget(self._lbl_errors)
        lyt_main.addLayout(lyt_buttons)
        self.setLayout(lyt_main)

    def _build_connections(self):
        self._btn_cancel.clicked.connect(self.reject)
        self._btn_import.clicked.connect(self._import_assets)

    def _setup_ui(self):
        self.setWindowTitle('Import Assets')
        self._edit_path.setPlaceholderText('Top Level Folder Path')
        self._edit_types.setPlaceholderText('List of types in form of "fbx,mov,jpg"')
        self.setMinimumWidth(600)

    def _import_assets(self):
        path = self._edit_path.text()
        if not os.path.isdir(path):
            self._lbl_errors.setText('Folder does not exist.')
            return

        types_str = self._edit_types.text().strip()
        types = list()
        if types_str:
            types = [x.strip() for x in types_str.split(',')]

        if not import_directory_tree(path, types):
            return

        self.accept()


def import_directory_tree(path, extensions):
    if extensions:
        extensions = ['.' + x.lstrip('.').lower() for x in extensions[:]]

    found = list()
    for root, dir, files in os.walk(path):
        for name in files:
            prefix, ext = os.path.splitext(name)
            if extensions and ext.lower() not in extensions:
                continue
            found.append(os.path.join(root, name).replace('\\', '/'))

    engine = get_engine()

    if found:
        existing_paths = engine.select(Query('path', filepath=found))
        _paths = [x.filepath for x in existing_paths]
        found = list(set(found) - set(_paths))

    types_found = set()
    for item in found:
        e = os.path.splitext(item)[-1]
        types_found.add(e.strip('.') or 'n/a')

    res = QMessageBox.question(None, 'Found Items',
                               '%d files found, continue?\n%s' % (len(found), ','.join(types_found)),
                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)

    if res != QMessageBox.Yes:
        return False

    if not found:
        return False

    # Create assets
    assets = list()
    for path in found:
        filename = os.path.basename(path)
        asset_name, ext = os.path.splitext(filename)
        assets.append(AssetModel(name=asset_name))
    engine.create_many(assets)

    # Create paths
    paths = list()
    for asset, path in zip(assets, found):
        paths.append(PathModel(asset.id, path))
    engine.create_many(paths)

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
