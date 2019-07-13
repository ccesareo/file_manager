from file_manager.data.connection import get_engine
# noinspection PyUnresolvedReferences
from file_manager.data.entities import *

engine = get_engine()
for model in BaseEntity.__subclasses__():
    engine.setup_entity(model)
