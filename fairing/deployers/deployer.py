from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import abc 
import six

@six.add_metaclass(abc.ABCMeta)
class DeployerInterface(object):
    """Deploys a training job to the cluster"""

    def deploy(self, pod_template_spec):
        """Deploys the training job"""
        raise NotImplementedError('TrainingInterface.deploy')

    @abc.abstractmethod
    def get_logs(self):
        """Streams the logs for the training job"""
        raise NotImplementedError('TrainingInterface.train')
