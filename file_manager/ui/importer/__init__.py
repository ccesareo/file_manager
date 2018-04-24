import os

from file_manager.config import LOG
from file_manager.data.connection import get_engine
from file_manager.data.models.asset import AssetModel
from file_manager.data.models.path import PathModel
from file_manager.data.models.tag_to_asset import TagToAssetModel
from file_manager.data.models.tag import TagModel
from file_manager.data.query import Query


def import_directory_tree(path, extensions):
    if extensions:
        extensions = ['.' + x.lstrip('.').lower() for x in extensions[:]]

    found = list()
    for root, dir, files in os.walk(path):
        for name in files:
            prefix, ext = os.path.splitext(name)
            if extensions and ext.lower() not in extensions:
                continue
            found.append(os.path.join(root, name).replace('\\', '/'))

    engine = get_engine()

    if found:
        existing_paths = engine.select(Query('path', filepath=found))
        _paths = [x.filepath for x in existing_paths]
        found = list(set(found) - set(_paths))

    # Create assets
    assets = list()
    for path in found:
        filename = os.path.basename(path)
        asset_name, ext = os.path.splitext(filename)
        assets.append(AssetModel(name=asset_name))
    engine.create_many(assets)

    # Create paths
    paths = list()
    for asset, path in zip(assets, found):
        paths.append(PathModel(asset.id, path))
    engine.create_many(paths)

    # Create tags
    _tags = engine.select(Query('tag', name='new'))
    if not _tags:
        LOG.info('Creating "new" tag.')
        tag = TagModel('new')
        engine.create(tag)
    else:
        tag = _tags[0]

    tags_to_assets = list()
    for asset in assets:
        tags_to_assets.append(TagToAssetModel(asset.id, tag.id))
    engine.create_many(tags_to_assets)


import_directory_tree('C:\\code', list())
