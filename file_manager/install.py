from file_manager.config import settings
from file_manager.data.base_model import BaseModel
from file_manager.data.connection import get_engine
# noinspection PyUnresolvedReferences
from file_manager.data.models import *

engine = get_engine(settings.db_engine)
for model in BaseModel.__subclasses__():
    engine.setup_model(model)
