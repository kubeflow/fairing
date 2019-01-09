
from ..native import decorators
from .deployment import KubeflowDeployment
 
class Training(decorators.Training):

    def __init__(self, namespace=None):
        super(Training, self).__init__(namespace)
        self.distribution = {
            'Worker': 1
        }

    def _deploy(self, user_object):
        deployment = KubeflowDeployment(
            self.namespace,
            self.runs,
            self.distribution)
        deployment.execute()


class DistributedTraining(Training):

    def __init__(self, worker_count=0, ps_count=0, namespace=None):
        # By default we set worker to 0 as we always add a Chief
        super(DistributedTraining, self).__init__(namespace)
        self.distribution = {
            'Worker': worker_count,
            'PS': ps_count,
            'Chief': 1
        }
    
