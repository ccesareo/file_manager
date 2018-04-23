from file_manager.data.base_model import BaseModel
from file_manager.data.models.asset import AssetModel
from file_manager.data.models.path import PathModel
from file_manager.data.models.tag import TagModel
from file_manager.data.models.tag_to_asset import TagToAssetModel


def find_model(name):
    for model in BaseModel.__subclasses__():
        if model.NAME == name:
            return model
    raise Exception('No model found for "%s".' % name)