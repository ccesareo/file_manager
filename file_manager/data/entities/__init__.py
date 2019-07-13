from ...data.base_entity import BaseEntity
from ...data.entities.asset import AssetEntity
from ...data.entities.path import PathEntity
from ...data.entities.tag import TagEntity
from ...data.entities.tag_to_asset import TagToAssetEntity


def find_entity(name):
    for entity in BaseEntity.__subclasses__():
        if entity.NAME == name:
            return entity
    raise Exception('No entity found for "%s".' % name)