import datetime
import getpass
import inspect

from file_manager.data.field import Field


class BaseModel(object):
    NAME = None  # Name of table
    id = Field(int)
    timestamp = Field(datetime.datetime)
    username = Field(str)

    @classmethod
    def fields(cls):
        values = inspect.getmembers(cls)
        fields = list()
        for name, attr in values:
            if isinstance(attr, Field):
                attr.name = name.strip('_')
                fields.append(attr)
        fields.sort(key=lambda _: _.order)
        return fields

    def __init__(self, **data):
        self._changes = dict()

        self.id = None
        self.username = getpass.getuser().lower()

        field_names = [field.name for field in self.fields()]
        for k, v in data.items():
            assert k in field_names, 'Field "%s" does not exist on %s' % (k, self)
            setattr(self, k, v)

    def __setattr__(self, key, value):
        old_value = getattr(self.__class__, key, None)
        super(BaseModel, self).__setattr__(key, value)

        attr = getattr(self.__class__, key, None)
        if isinstance(attr, Field):
            if value != old_value and key != 'id':
                # LOG.debug('Value changed to %s' % value)
                self._changes[key] = value

    def changes(self):
        return self._changes.copy()

    def clear_changes(self):
        self._changes = dict()

    def data(self):
        fields = self.fields()
        result = dict()
        for field in fields:
            result[field.name] = getattr(self, field.name)
        return result
