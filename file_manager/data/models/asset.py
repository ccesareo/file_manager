from file_manager.data.base_model import BaseModel
from file_manager.data.field import Field


class AssetModel(BaseModel):
    NAME = 'asset'

    name = Field(str)
