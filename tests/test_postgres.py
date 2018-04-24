from file_manager.data.engines.postgres import PsycoPGEngine
from file_manager.data.models.tag import TagModel
from file_manager.data.models.asset import AssetModel

PsycoPGEngine.setup_model(TagModel)

for i in range(100):
    example = AssetModel()
    example.name = 'Asset%03d' % i
    PsycoPGEngine.create(example)
