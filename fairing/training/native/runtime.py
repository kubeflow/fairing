from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

class BasicNativeRuntime(object):
    """BasicNativeRuntime represents the behavior of the code while training
        during a simple training job"""

    def execute(self, user_object):
        if 'build' in dir(user_object) and callable(getattr(user_object, 'build')):
            user_object.build()
        user_object.train()
