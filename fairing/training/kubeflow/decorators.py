
from ..native import decorators
from .deployment import KubeflowDeployment
 
class Training(decorators.Training):

    def __init__(self, namespace=None):
        super(Training, self).__init__(namespace)
    
    def _deploy(self, user_object):
        deployment = KubeflowDeployment(self.namespace, self.runs)
        deployment.execute()

    
