from .base_entity import BaseEntity
from ..connection import get_engine
from ..field import Field
from ..query import Query


class TagToAssetEntity(BaseEntity):
    NAME = 'tag_to_asset'

    tag_id = Field(int)
    asset_id = Field(int)

    def __init__(self, asset_id, tag_id, **kwargs):
        super(TagToAssetEntity, self).__init__(**kwargs)

        self.asset_id = asset_id
        self.tag_id = tag_id

    @classmethod
    def apply_tags(cls, asset_records, tag_records):
        existing = cls._find_existing(asset_records, tag_records)

        all_pairs = set()
        for asset in asset_records:
            for tag in tag_records:
                all_pairs.add((asset.id, tag.id))
        for item in existing:
            all_pairs.remove((item.asset_id, item.tag_id))

        if not all_pairs:
            return

        entities = list()
        for asset_id, tag_id in all_pairs:
            entities.append(TagToAssetEntity(asset_id, tag_id))

        engine = get_engine()
        engine.create_many(entities)

    @classmethod
    def remove_tags(cls, asset_records, tag_records):
        existing = cls._find_existing(asset_records, tag_records)
        engine = get_engine()
        engine.delete_many(existing)

    @classmethod
    def find_assets(cls, tag_records):
        tag_ids = [record.id for record in tag_records]

        engine = get_engine()
        links = engine.select(Query('tag_to_asset', tag_id=tag_ids))
        asset_ids = [l.asset_id for l in links]
        return engine.select(Query('asset', id=asset_ids))

    @classmethod
    def _find_existing(cls, asset_records, tag_records):
        asset_ids = [x.id for x in asset_records]
        tag_ids = [x.id for x in tag_records]

        q = Query('tag_to_asset')
        q.start_filter_group(q.OP.OR)
        for asset_id in asset_ids:
            for tag_id in tag_ids:
                q.start_filter_group(q.OP.AND)
                q.add_filter('asset_id', asset_id)
                q.add_filter('tag_id', tag_id)
                q.end_filter_group()
        q.end_filter_group()

        engine = get_engine()
        return engine.select(q)
