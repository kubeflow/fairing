from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import abc
import six

@six.add_metaclass(abc.ABCMeta)
class ContextSourceInterface(object):

    @abc.abstractmethod
    def prepare(self):
        raise NotImplementedError('ContextSourceInterface.setup')

    @abc.abstractmethod
    def cleanup(self):
        raise NotImplementedError('ContextSourceInterface.cleanup')
        
    @abc.abstractmethod
    def generate_pod_spec(self, pod_spec): 
        raise NotImplementedError('ContextSourceInterface.modify_pod_spec')
