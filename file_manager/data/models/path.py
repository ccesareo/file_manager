import os

from file_manager.data.base_model import BaseModel
from file_manager.data.field import Field


class PathModel(BaseModel):
    NAME = 'path'

    asset_id = Field(int)
    filepath = Field(str)
    sub_folders = Field(str)
    type = Field(str)

    def __init__(self, asset_id, filepath, sub_folders, **kwargs):
        """
        :type asset: file_manager.data.models.asset.AssetModel
        :type filepath: str
        :type sub_folders: str
        """
        super(PathModel, self).__init__(**kwargs)

        self.asset_id = asset_id
        self.filepath = filepath.replace('\\', '/')
        self.sub_folders = sub_folders or None
        self.type = os.path.splitext(filepath)[1].strip('.')
