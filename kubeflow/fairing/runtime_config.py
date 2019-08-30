

class RuntimeConfig(object):
    """A passthrough config shim that runs in the fairing runtime"""
    def __init__(self):
        pass

    def set_preprocessor(self, name, **kwargs): #pylint:disable=unused-argument
        self._preprocessor = name

    def get_preprocessor(self):
        return self._preprocessor

    def set_builder(self, name, **kwargs): #pylint:disable=unused-argument
        self._builder = name

    def get_builder(self):
        return self._builder

    def set_deployer(self, name, **kwargs): #pylint:disable=unused-argument
        self._deployer = name

    def get_deployer(self, **kwargs): #pylint:disable=unused-argument
        return self._deployer

    def run(self):
        pass

    def reset(self):
        pass

    def fn(self, func): #pylint:disable=no-self-use
        return func

config = RuntimeConfig()
