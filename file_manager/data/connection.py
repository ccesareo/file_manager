from ..config import settings


def get_engine():
    """
    :rtype: file_manager.data.base_engine.BaseEngine
    """
    engine_name = settings.db_engine
    if engine_name == 'postgresql':
        from ..data.engines.postgres import PsycoPGEngine
        return PsycoPGEngine
    elif engine_name == 'sqlite':
        from ..data.engines.sqlite import SqliteEngine
        return SqliteEngine
    else:
        raise Exception('No engine found for "%s"' % engine_name)
