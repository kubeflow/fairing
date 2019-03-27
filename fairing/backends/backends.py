from fairing.deployers.gcp.gcp import GCPJob
from fairing.deployers.gcp.gcpserving import GCPServingDeployer
from fairing.deployers.job.job import Job
from fairing.deployers.tfjob.tfjob import TfJob
from fairing.deployers.serving.serving import Serving
from fairing.cloud import gcp


class KubernetesBackend:

    def __init__(self):
        pass
    
    def get_training_deployer(self):
            return Job()
    
    def get_serving_deployer(self, model_class):
            return Serving(model_class)

class GKEBackend(KubernetesBackend):

    def __init__(self):
        super(GKEBackend, self).__init__()
    
    def get_training_deployer(self):
            return Job(pod_spec_mutators=[gcp.add_gcp_credentials])
    
    def get_serving_deployer(self, model_class):
            return Serving(model_class)

class KubeflowBackend(KubernetesBackend):

    def __init__(self):
        super(KubeflowBackend, self).__init__()
    
    def get_training_deployer(self,ml_task_type):
            return TfJob(pod_spec_mutators=[gcp.add_gcp_credentials])

class KubeflowGKEBackend(GKEBackend):

    def __init__(self):
        super(KubeflowGKEBackend, self).__init__()
    
    def get_training_deployer(self,ml_task_type):
            return TfJob(pod_spec_mutators=[gcp.add_gcp_credentials])

class GCPManagedBackend(KubernetesBackend):

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
