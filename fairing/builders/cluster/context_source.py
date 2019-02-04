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
    """An interface that provides the build context to the in cluster builder"""
    
    @abc.abstractmethod
    def prepare(self):
        """Makes the context somehow available for use in the pod spec (by uploading, etc.)"""
        raise NotImplementedError('ContextSourceInterface.setup')

    @abc.abstractmethod
    def cleanup(self):
        """Cleans up the context after the build is complete"""
        raise NotImplementedError('ContextSourceInterface.cleanup')
        
    @abc.abstractmethod
    def generate_pod_spec(self, pod_spec):
        """Generates a pod spec for building the image in the cluster, pointing to the prepared build context"""
        raise NotImplementedError('ContextSourceInterface.modify_pod_spec')
