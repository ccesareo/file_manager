from file_manager.data.base_model import BaseModel
from file_manager.data.connection import get_engine
from file_manager.data.field import Field
from file_manager.data.query import Query


class TagToAssetModel(BaseModel):
    NAME = 'tag_to_asset'

    tag_id = Field(int)
    asset_id = Field(int)

    def __init__(self, asset_id, tag_id, **kwargs):
        super(TagToAssetModel, self).__init__(**kwargs)

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

        engine = get_engine()
        for asset_id, tag_id in all_pairs:
            engine.create(TagToAssetModel(asset_id, tag_id))

    @classmethod
    def remove_tags(cls, asset_records, tag_records):
        existing = cls._find_existing(asset_records, tag_records)
        engine = get_engine()
        for record in existing:
            engine.delete(record)

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
