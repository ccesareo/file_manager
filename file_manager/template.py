import hashlib
import imp
import os

from .config import settings


class ParsingTemplate(object):
    def __init__(self, template_name):
        _path = os.path.join(settings.templates_folder, template_name)
        _uniq = hashlib.sha1(_path).hexdigest()
        self._mod = imp.load_source('template%s' % _uniq, _path)

    def get_asset_name(self, file_path):
        file_name = os.path.basename(file_path)
        asset_name = os.path.splitext(file_name)[0]
        if self._mod and hasattr(self._mod, 'get_asset_name'):
            asset_name = self._mod.get_asset_name(file_path) or asset_name
        return asset_name

    def get_thumbnail(self, file_path):
        thumbnail = None
        if self._mod and hasattr(self._mod, 'get_thumbnail'):
            thumbnail = self._mod.get_thumbnail(file_path)
        return thumbnail

    def get_tags(self, file_path):
        tags = ['new']
        if self._mod and hasattr(self._mod, 'get_tags'):
            tags = self._mod.get_tags(file_path)
        return tags
