import abc 
import six

from fairing.deployers.gcp.gcp import GCPJob
from fairing.deployers.gcp.gcpserving import GCPServingDeployer
from fairing.deployers.job.job import Job
from fairing.deployers.tfjob.tfjob import TfJob
from fairing.deployers.serving.serving import Serving
from fairing.cloud import gcp


@six.add_metaclass(abc.ABCMeta)
class BackendInterface(object):

    @abc.abstractmethod
    def get_training_deployer(self):
        """Deploys the training job"""
        raise NotImplementedError('TrainingInterface.deploy')

    @abc.abstractmethod
    def get_serving_deployer(self, model_class):
        """Streams the logs for the training job"""
        raise NotImplementedError('TrainingInterface.train')

class KubernetesBackend(BackendInterface):

    def __init__(self, namespace=None):
        self._namespace = namespace
    
    def get_training_deployer(self):
        return Job(self._namespace)
    
    def get_serving_deployer(self, model_class):
        return Serving(model_class, namespace=self._namespace)

class GKEBackend(KubernetesBackend):

    def __init__(self, namespace=None):
        super(GKEBackend, self).__init__(namespace)
    
    def get_training_deployer(self):
        return Job(namespace=self._namespace, pod_spec_mutators=[gcp.add_gcp_credentials_if_exists])
    
    def get_serving_deployer(self, model_class):
        return Serving(model_class, namespace=self._namespace)

class KubeflowBackend(KubernetesBackend):

    def __init__(self, namespace="kubeflow"):
        super(KubeflowBackend, self).__init__(namespace)
    
    def get_training_deployer(self):
        return TfJob(namespace=self._namespace)

class KubeflowGKEBackend(GKEBackend):

    def __init__(self, namespace="kubeflow"):
        super(KubeflowGKEBackend, self).__init__(namespace)
    
    def get_training_deployer(self):
        return TfJob(namespace=self._namespace, pod_spec_mutators=[gcp.add_gcp_credentials_if_exists])

class GCPManagedBackend(BackendInterface):

    def __init__(self, project_id=None, region=None, training_scale_tier=None):
        super(GCPManagedBackend, self).__init__()
        self._project_id = project_id or gcp.guess_project_name()
        self._region = region or 'us-central1'
        self._training_scale_tier =  training_scale_tier or 'BASIC'
    
    def get_training_deployer(self):
        return GCPJob(self._project_id, self._region, self._training_scale_tier)

    def get_serving_deployer(self, model_class):
        # currently GCP serving deployer doesn't implement deployer interface
        raise NotImplementedError("GCP managed serving is not implemented.")
