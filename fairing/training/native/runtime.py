from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from fairing.training import base

class NativeRuntime(base.RuntimeInterface):
    def execute(self, user_object):
        if 'build' in dir(user_object) and callable(getattr(user_object, 'build')):
            user_object.build()
        user_object.train()