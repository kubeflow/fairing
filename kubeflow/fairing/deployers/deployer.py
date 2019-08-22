import abc
import six


@six.add_metaclass(abc.ABCMeta)
class DeployerInterface(object):
    """Deploys a training job to the cluster"""

    def deploy(self, pod_template_spec):
        """Deploys the training job

        :param pod_template_spec: pod template spec

        """
        raise NotImplementedError('TrainingInterface.deploy')

    @abc.abstractmethod
    def get_logs(self):
        """Streams the logs for the training job"""
        raise NotImplementedError('TrainingInterface.train')
