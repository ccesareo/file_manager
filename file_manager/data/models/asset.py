from file_manager.data.base_model import BaseModel
from file_manager.data.connection import get_engine
from file_manager.data.field import Field
from file_manager.data.models.tag_to_asset import TagToAssetModel
from file_manager.data.query import Query


class AssetModel(BaseModel):
    NAME = 'asset'

    name = Field(str)

    @classmethod
    def delete(cls, records):
        asset_ids = [_.id for _ in records]
        engine = get_engine()
        links = engine.select(Query('tag_to_asset', asset_id=asset_ids))
        paths = engine.select(Query('path', asset_id=asset_ids))
        for item in (links + paths + records):
            # TODO - delete multiple by table
            engine.delete(item)

    @classmethod
    def merge(cls, asset_records, new_name):
        asset_ids = [_.id for _ in asset_records]

        engine = get_engine()

        asset = AssetModel(name=new_name)
        engine.create(asset)

        links = engine.select(Query('tag_to_asset', asset_id=asset_ids))
        if links:
            tags = engine.select(Query('tag', id=[_.tag_id for _ in links]))
            if tags:
                TagToAssetModel.apply_tags([asset], tags)

        paths = engine.select(Query('path', asset_id=asset_ids))
        for path in paths:
            path.asset_id = asset.id
            engine.update(path)

        AssetModel.delete(asset_records)
        return asset
