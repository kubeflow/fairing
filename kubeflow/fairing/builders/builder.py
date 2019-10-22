import abc
import six

@six.add_metaclass(abc.ABCMeta)
class BuilderInterface(object):

    @abc.abstractmethod
    def build(self):
        """Will be called when the build needs to start"""
        raise NotImplementedError('BuilderInterface.build')

    @abc.abstractmethod
    def generate_pod_spec(self):
        """This method should return a V1PodSpec with the correct image set.
            This is also where the builder should set the environment variables
            and volume/volumeMounts that it may need to work

        """
        raise NotImplementedError('BuilderInterface.generate_pod_spec')
