from file_manager.data.connection import get_engine
# noinspection PyUnresolvedReferences
from file_manager.data.models import *

engine = get_engine()
for model in BaseModel.__subclasses__():
    engine.setup_model(model)
