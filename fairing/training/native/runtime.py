from fairing.training import base

class NativeRuntime(base.RuntimeInterface):
    def execute(self, user_object):
        raise NotImplementedError()