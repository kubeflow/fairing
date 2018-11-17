from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import logging
logging.basicConfig(format='%(message)s')

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
