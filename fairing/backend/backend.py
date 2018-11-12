from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import object

import json
import os
import subprocess


class Backend(object):
    def add_tensorboard(self, svc, name, tensorboard_options):
        raise NotImplementedError()

    def compile_serving_ast(self, img, name, port, replicas):
        raise NotImplementedError()

    def stream_logs(self, image_name, image_tag):
        raise NotImplementedError()