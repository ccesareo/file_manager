from file_manager.data.base_model import BaseModel
from file_manager.data.field import Field


class ApplicationModel(BaseModel):
    NAME = 'path'

    name = Field(str)
    file_type = Field(str)

    def __init__(self, name, file_type, **kwargs):
        """
        :type name: str
        :param name: Name of application
        :type file_type: str
        :param file_type: File type to associate
        """
        super(ApplicationModel, self).__init__(**kwargs)

        self.name = name
        self.file_type = file_type
