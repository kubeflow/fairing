import abc 
import six

@six.add_metaclass(abc.ABCMeta)
class BuilderInterface(object):

    @abc.abstractmethod
    def execute(self): pass

    @abc.abstractmethod
    def generate_pod_spec(self): pass
