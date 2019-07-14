import glob
import imp
import os
import threading

from Qt import QtCore, QtWidgets
from ..config import settings
from ..data.connection import get_engine
from ..data.entities.asset import AssetEntity
from ..data.entities.path import PathEntity
from ..data.entities.tag import TagEntity
from ..data.entities.tag_to_asset import TagToAssetEntity
from ..data.query import Query
from ..ui.widgets.dialogs import ask


class FoundPathEvent(QtCore.QEvent):
    def __init__(self, count):
        super(FoundPathEvent, self).__init__(self.Type(self.registerEventType()))

        self.count = count


class ResultEvent(QtCore.QEvent):
    def __init__(self, paths):
        super(ResultEvent, self).__init__(self.Type(self.registerEventType()))

        self.paths = paths


class SearchThread(threading.Thread):
    def __init__(self, wdg, root_path, template, types_str):
        super(SearchThread, self).__init__()

        self._wdg = wdg
        self._root_path = root_path
        self._template = template

        self._extensions = [x.strip() for x in types_str.split(',')] if types_str else list()

        self._cancel = False

    def stop(self):
        self._cancel = True

    def run(self):
        if self._extensions:
            self._extensions = ['.' + x.lstrip('.').lower() for x in self._extensions[:]]

        module = imp.load_source('template', self._template) if self._template else None

        found = list()
        for root, d, files in os.walk(self._root_path):
            if self._cancel:
                break
            QtWidgets.QApplication.postEvent(self._wdg, FoundPathEvent(len(found)))
            for name in files:
                ext = os.path.splitext(name)[1]
                if self._extensions and ext.lower() not in self._extensions:
                    continue

                found_path = os.path.join(root, name).replace('\\', '/')
                if module and hasattr(module, 'is_valid'):
                    if not module.is_valid(found_path):
                        continue

                found.append(found_path)
        else:
            QtWidgets.QApplication.postEvent(self._wdg, ResultEvent(found))


class AssetImporter(QtWidgets.QDialog):
    CACHED_PATH = None

    def __init__(self, *args, **kwargs):
        super(AssetImporter, self).__init__(*args, **kwargs)

        self._lbl_info = QtWidgets.QLabel()
        self._thread = None

        self._edit_path = QtWidgets.QLineEdit()
        self._btn_browse = QtWidgets.QPushButton('...')
        self._edit_types = QtWidgets.QLineEdit()
        self._cmbo_templates = QtWidgets.QComboBox()

        self._btn_import = QtWidgets.QPushButton('Import Assets')
        self._btn_cancel = QtWidgets.QPushButton('Cancel')

        self._build_ui()
        self._build_connections()
        self._setup_ui()

    def event(self, event):
        if isinstance(event, ResultEvent):
            if import_directory_tree(self._edit_path.text().replace('\\', '/'),
                                     self._current_template(),
                                     event.paths):
                self.accept()
            else:
                self._btn_import.setEnabled(True)

        elif isinstance(event, FoundPathEvent):
            self._lbl_info.setText('%d found.' % event.count)
        else:
            return super(AssetImporter, self).event(event)

        return True

    def _build_ui(self):
        lyt_editors = QtWidgets.QGridLayout()
        lyt_editors.addWidget(QtWidgets.QLabel('Folder Path'), 0, 0)
        lyt_editors.addWidget(self._edit_path, 0, 1)
        lyt_editors.addWidget(self._btn_browse, 0, 2)
        lyt_editors.addWidget(QtWidgets.QLabel('File Types'), 1, 0)
        lyt_editors.addWidget(self._edit_types, 1, 1)
        lyt_editors.addWidget(QtWidgets.QLabel('Template'), 2, 0)
        lyt_editors.addWidget(self._cmbo_templates, 2, 1)

        lyt_buttons = QtWidgets.QHBoxLayout()
        lyt_buttons.addWidget(self._btn_import)
        lyt_buttons.addWidget(self._btn_cancel)

        lyt_main = QtWidgets.QVBoxLayout()
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

        templates = glob.glob(settings.templates_folder + '\\*.py')
        templates.sort()
        templates = [os.path.basename(p) for p in templates]
        if 'default.py' in templates:
            templates.remove('default.py')
            templates.insert(0, 'default.py')
        self._cmbo_templates.addItems(templates)

    def _browse_files(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Choose Root Folder')
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
        template = self._current_template()

        AssetImporter.CACHED_PATH = path

        if not os.path.isdir(path):
            self._lbl_info.setText('Folder does not exist.')
            return

        if self._thread is not None:
            self._thread.stop()
            self._thread.join()

        self._thread = SearchThread(self, path, template, self._edit_types.text().strip())
        self._thread.start()

        self._btn_import.setEnabled(False)

    def _current_template(self):
        template = None
        if self._cmbo_templates.currentText():
            template = os.path.join(settings.templates_folder, self._cmbo_templates.currentText())
        return template


def import_directory_tree(root_path, template, paths):
    engine = get_engine()

    if paths:
        existing_paths = engine.select(Query('path', filepath=paths))
        _paths = [x.filepath for x in existing_paths]
        paths = list(set(paths) - set(_paths))

    types_found = set()
    for item in paths:
        e = os.path.splitext(item)[-1]
        types_found.add(e.strip('.') or 'n/a')

    if not ask('Found Items', '%d new files found, continue?\n%s' % (len(paths), ','.join(types_found))):
        return False

    if not paths:
        return False

    module = imp.load_source('template', template) if template else None

    # Create assets
    for path in paths:
        filename = os.path.basename(path)

        # Get Asset Name
        asset_name = os.path.splitext(filename)[0]
        if module and hasattr(module, 'get_asset_name'):
            asset_name = module.get_asset_name(path) or asset_name

        # Get Tags
        tags = ['new']
        if module and hasattr(module, 'get_tags'):
            tags = module.get_tags(path)

        # Get Thumbnail
        thumbnail = None
        if module and hasattr(module, 'get_thumbnail'):
            thumbnail = module.get_thumbnail(path)

        path_rec = None
        created_tags = list()

        # Create Asset
        asset_rec = engine.create(AssetEntity(name=asset_name))
        """:type: file_manager.data.entities.asset.AssetEntity"""

        try:
            # Asset Paths
            _sub_folders = path.replace(root_path, '').lstrip('/').rsplit('/', 1)[0]
            path_rec = engine.create(PathEntity(asset_rec.id, path, _sub_folders))

            # Create New Tags
            _q = Query('tag', name='new')
            _q.add_filter('name', tags, operator=_q.OP.ISIN)
            tag_recs = engine.select(_q)
            _new_tags = set(tags) - {t.name for t in tag_recs}
            for new_tag in _new_tags:
                _new_tag_rec = engine.create(TagEntity(new_tag))
                created_tags.append(_new_tag_rec)
            tag_recs += created_tags

            # Assign Tags
            tags_to_assets = list()
            for tag_rec in tag_recs:
                tags_to_assets.append(TagToAssetEntity(asset_rec.id, tag_rec.id))
            engine.create_many(tags_to_assets)

            # Assign Thumbnail
            if thumbnail:
                asset_rec.assign_thumbnail(thumbnail)

        except:
            # Revert Creation
            if path_rec:
                engine.delete(path_rec)
            if created_tags:
                engine.delete_many(created_tags)
            engine.delete(asset_rec)
            raise

    return True
