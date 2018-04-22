class BaseEngine(object):
    @classmethod
    def setup_model(cls, model_class):
        raise NotImplementedError()

    @classmethod
    def create(cls, model):
        raise NotImplementedError()

    @classmethod
    def select(cls, **kwargs):
        raise NotImplementedError()

    @classmethod
    def update(cls, model):
        raise NotImplementedError()

    @classmethod
    def delete(cls, model):
        raise NotImplementedError()
