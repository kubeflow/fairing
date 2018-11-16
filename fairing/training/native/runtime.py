from fairing.training import base

class NativeRuntime(base.RuntimeInterface):
    def execute(self, user_object):
        if 'build' in dir(user_object) and callable(getattr(user_object, 'build')):
            user_object.build()
        user_object.train()