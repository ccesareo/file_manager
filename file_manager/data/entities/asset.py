import os

from ...config import settings
from ...data.base_entity import BaseEntity
from ...data.connection import get_engine
from ...data.field import Field
from ...data.entities.tag_to_asset import TagToAssetEntity
from ...data.query import Query


class AssetEntity(BaseEntity):
    NAME = 'asset'

    name = Field(str)
    thumbnail = Field(str)

    @classmethod
    def delete(cls, records):
        asset_ids = [_.id for _ in records]
        engine = get_engine()
        links = engine.select(Query('tag_to_asset', asset_id=asset_ids)) if asset_ids else list()
        paths = engine.select(Query('path', asset_id=asset_ids)) if asset_ids else list()

        engine.delete_many(links)
        engine.delete_many(paths)
        engine.delete_many(records)

        for record in records:
            if record.thumbnail:
                folder = settings.thumbs_folder()
                path = os.path.join(folder, record.thumbnail)
                if os.path.isfile(path):
                    os.remove(path)

    @classmethod
    def merge(cls, asset_records, new_name):
        asset_ids = [_.id for _ in asset_records]

        engine = get_engine()

        asset = AssetEntity(name=new_name)
        engine.create(asset)

        links = engine.select(Query('tag_to_asset', asset_id=asset_ids))
        if links:
            tags = engine.select(Query('tag', id=[_.tag_id for _ in links]))
            if tags:
                TagToAssetEntity.apply_tags([asset], tags)

        paths = engine.select(Query('path', asset_id=asset_ids))
        for path in paths:
            path.asset_id = asset.id
            engine.update(path)

        AssetEntity.delete(asset_records)
        return asset
