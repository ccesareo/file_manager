import os

from file_manager.data.base_model import BaseModel
from file_manager.data.field import Field


class PathModel(BaseModel):
    NAME = 'path'

    asset_id = Field(int)
    filepath = Field(str)
    type = Field(str)

    def __init__(self, asset_id, filepath, **kwargs):
        """
        :type asset: file_manager.data.models.asset.AssetModel
        :type filepath: str
        """
        super(PathModel, self).__init__(**kwargs)

        self.asset_id = asset_id
        self.filepath = filepath.replace('\\', '/')
        self.type = os.path.splitext(filepath)[1].strip('.')
