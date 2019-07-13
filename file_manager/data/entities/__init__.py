from file_manager.data.base_entity import BaseEntity
from file_manager.data.entities.asset import AssetEntity
from file_manager.data.entities.path import PathEntity
from file_manager.data.entities.tag import TagEntity
from file_manager.data.entities.tag_to_asset import TagToAssetEntity


def find_entity(name):
    for entity in BaseEntity.__subclasses__():
        if entity.NAME == name:
            return entity
    raise Exception('No entity found for "%s".' % name)