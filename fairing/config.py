from fairing import builders


class Config(object):
    def __init__(self):
        # TODO: load default configuration from K8s ConfigMap
        self._builder = None

    def set_builder(self, builder):
        if not isinstance(builder, builders.BuilderInterface):
            raise TypeError(
                'builder must be a BuilderInterface, but got %s' 
                % type(builder))
        self._builder = builder
    
    def get_builder(self):
        return self._builder

config = Config()
