import weakref

from PySide.QtCore import Signal

_CACHE = weakref.WeakValueDictionary()


class AssetModel(object):
    name_changed = Signal()
    tags_changed = Signal()

    def __new__(cls, record):
        # Only keep one instance per id for easier signaling of changes
        if record.id in _CACHE:
            return _CACHE[record.id]
        _CACHE[record.id] = _res = super(AssetModel, cls).__new__(cls, record)
        return _res

    def __init__(self, record):
        """
        Args:
            record (file_manager.data.entities.asset.AssetEntity):
        """
        super(AssetModel, self).__init__()

        self._record = record

    @property
    def name(self):
        return self._record.name

    def tags(self):
        raise NotImplementedError()
