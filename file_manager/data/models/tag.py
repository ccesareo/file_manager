import random

from file_manager.data.base_model import BaseModel
from file_manager.data.field import Field


class TagModel(BaseModel):
    NAME = 'tag'

    name = Field(str)
    fg_color = Field(str)
    bg_color = Field(str)

    def __init__(self, name, **kwargs):
        super(TagModel, self).__init__(**kwargs)

        self.name = name
        if 'bg_color' not in kwargs:
            self.bg_color = '#%s' % ('%030x' % random.randrange(16 ** 30))[-6:]
        if 'fg_color' not in kwargs:
            self.fg_color = '#%s' % ('%030x' % random.randrange(16 ** 30))[-6:]
