def get_engine(engine_name):
    if engine_name == 'postgresql':
        from file_manager.data.engines.postgres import PsycoPGEngine
        return PsycoPGEngine
    else:
        raise Exception('No engine found for "%s"' % engine_name)
