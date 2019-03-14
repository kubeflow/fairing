

class RuntimeConfig(object):
    """A passthrough config shim that runs in the fairing runtime"""
    def __init__(self):
        pass

    def set_preprocessor(self, name, **kwargs):
        self._preprocessor = name

    def get_preprocessor(self):
        return self._preprocessor

    def set_builder(self, name, **kwargs):
        self._builder = name

    def get_builder(self):
        return self._builder

    def set_deployer(self, name, **kwargs):
        self._deployer = name

    def get_deployer(self, **kwargs):
        return self._deployer

    def get_model(self):
        return self._model

    def set_model(self, model):
        self._model = model

    def run(self):
        pass

    def reset(self):
        pass
    
    def fn(self, func):
        return func

config = RuntimeConfig()
