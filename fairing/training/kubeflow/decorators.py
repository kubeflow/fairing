
from ..native import decorators
from .deployment import KubeflowDeployment


class Training(decorators.Training):

    def __init__(self, namespace=None, job_name=None):
        super(Training, self).__init__(namespace, job_name)
        self.distribution = {
            'Worker': 1
        }

    def _deploy(self, user_object):
        deployment = KubeflowDeployment(
            self.namespace,
            self.job_name,
            self.runs,
            self.distribution)
        deployment.execute()


class DistributedTraining(Training):

    def __init__(self, worker_count=0, ps_count=0, namespace=None, job_name=None):
        # By default we set worker to 0 as we always add a Chief
        super(DistributedTraining, self).__init__(namespace, job_name)
        self.distribution = {
            'Worker': worker_count,
            'PS': ps_count,
            'Chief': 1
        }
    
