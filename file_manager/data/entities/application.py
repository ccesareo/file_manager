from .base_entity import BaseEntity
from ..field import Field


class ApplicationEntity(BaseEntity):
    NAME = 'application'

    name = Field(str)
    executable_win = Field(str)
    file_type = Field(str)
    icon = Field(str)

    def __init__(self, name, file_type, **kwargs):
        """
        :type name: str
        :param name: Name of application
        :type file_type: str
        :param file_type: File type to associate
        """
        super(ApplicationEntity, self).__init__(**kwargs)

        self.name = name
        self.file_type = file_type
