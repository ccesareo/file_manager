import random

from .base_entity import BaseEntity
from ..connection import get_engine
from ..field import Field
from ..query import Query


class TagEntity(BaseEntity):
    NAME = 'tag'

    name = Field(str)
    fg_color = Field(str)
    bg_color = Field(str)

    @classmethod
    def delete(cls, records):
        if not records:
            return

        engine = get_engine()

        tag_ids = [_.id for _ in records]
        tag_to_assets = engine.select(Query('tag_to_asset', tag_id=tag_ids))
        engine.delete_many(tag_to_assets)
        engine.delete_many(list(records))

    def __init__(self, name, **kwargs):
        super(TagEntity, self).__init__(**kwargs)

        self.name = name
        if 'bg_color' not in kwargs:
            self.bg_color = '#%s' % ('%030x' % random.randrange(16 ** 30))[-6:]
        if 'fg_color' not in kwargs:
            self.fg_color = '#%s' % ('%030x' % random.randrange(16 ** 30))[-6:]
