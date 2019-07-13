class BaseEngine(object):
    @classmethod
    def setup_entity(cls, entity_class):
        raise NotImplementedError()

    @classmethod
    def create(cls, entity):
        raise NotImplementedError()

    @classmethod
    def create_many(cls, entities):
        raise NotImplementedError()

    @classmethod
    def select(cls, query):
        raise NotImplementedError()

    @classmethod
    def update(cls, entity):
        raise NotImplementedError()

    @classmethod
    def update_many(cls, entities):
        raise NotImplementedError()

    @classmethod
    def delete(cls, entity):
        raise NotImplementedError()

    @classmethod
    def delete_many(cls, entities):
        raise NotImplementedError()
