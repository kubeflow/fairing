import abc
import six


@six.add_metaclass(abc.ABCMeta)
class ContextSourceInterface(object):
    """Interface that provides the build context to the in cluster builder"""

    @abc.abstractmethod
    def prepare(self):
        """Makes the context somehow available for use in the pod spec"""
        raise NotImplementedError('ContextSourceInterface.setup')

    @abc.abstractmethod
    def cleanup(self):
        """Cleans up the context after the build is complete"""
        raise NotImplementedError('ContextSourceInterface.cleanup')

    @abc.abstractmethod
    def generate_pod_spec(self, pod_spec):
        """Generates a pod spec for building the image in the cluster, pointing to
        the prepared build context

        :param pod_spec: pod spec

        """
        raise NotImplementedError('ContextSourceInterface.modify_pod_spec')
