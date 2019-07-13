import weakref

from PySide.QtCore import Signal

_CACHE = weakref.WeakValueDictionary()


class TagModel(object):
    name_changed = Signal()
    color_changed = Signal()

    def __new__(cls, record):
        # Only keep one instance per id for easier signaling of changes
        if record.id in _CACHE:
            return _CACHE[record.id]
        _CACHE[record.id] = _res = super(TagModel, cls).__new__(cls, record)
        return _res

    def __init__(self, record):
        """
        Args:
            record (file_manager.data.entities.tag.TagEntity):
        """
        super(TagModel, self).__init__()

        self._record = record

    @property
    def name(self):
        return self._record.name

    @property
    def bg_color(self):
        return self._record.bg_color

    @property
    def fg_color(self):
        return self._record.fg_color
