import datetime


class Field(object):
    _ORDER = 0
    ALLOWED_TYPES = (str, int, float, datetime.date, datetime.datetime)

    def __init__(self, field_type):
        """
        :type field_type: data type
        :param field_type: Any one of (str, int, float, datetime.date, datetime.datetime)
        """
        self.name = None
        self.type = field_type
        self.order = Field._ORDER
        Field._ORDER += 1

        assert self.type in Field.ALLOWED_TYPES, 'Type "%s" is not allowed.' % self.type
