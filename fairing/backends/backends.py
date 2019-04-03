import abc 
import six

import fairing
from fairing.builders.docker.docker import DockerBuilder
from fairing.builders.cluster.cluster import ClusterBuilder
from fairing.builders.append.append import AppendBuilder
from fairing.deployers.gcp.gcp import GCPJob
from fairing.deployers.gcp.gcpserving import GCPServingDeployer
from fairing.deployers.job.job import Job
from fairing.deployers.serving.serving import Serving
from fairing.cloud import gcp
import fairing.ml_tasks.utils as ml_tasks_utils

@six.add_metaclass(abc.ABCMeta)
class BackendInterface(object):

    @abc.abstractmethod
    def get_builder(self, preprocessor, base_image, registry):
        """Creates a builder instance with right config for the given backend"""
        raise NotImplementedError('BackendInterface.get_builder')

    @abc.abstractmethod
    def get_training_deployer(self):
        """Creates a deployer to be used with a training job"""
        raise NotImplementedError('BackendInterface.get_training_deployer')

    @abc.abstractmethod
    def get_serving_deployer(self, model_class):
        """Creates a deployer to be used with a serving job"""
        raise NotImplementedError('BackendInterface.get_serving_deployer')

class KubernetesBackend(BackendInterface):

    def __init__(self, namespace=None):
        self._namespace = namespace
    
    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None):
        if fairing.utils.is_running_in_k8s():
            return ClusterBuilder(preprocessor=preprocessor,
                                  base_image=base_image,
                                  registry=registry,
                                  pod_spec_mutators=pod_spec_mutators,
                                  namespace=self._namespace)
        elif ml_tasks_utils.is_docker_daemon_exists():
            return DockerBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        else:
            # TODO (karthikv2k): Add more info on how to reolve this issue
            raise RuntimeError("Not able to guess the right builder for this job!")
    
    def get_training_deployer(self):
        return Job(self._namespace)
    
    def get_serving_deployer(self, model_class):
        return Serving(model_class, namespace=self._namespace)

class GKEBackend(KubernetesBackend):

    def __init__(self, namespace=None):
        super(GKEBackend, self).__init__(namespace)
    
    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
        return super(GKEBackend, self).get_builder(preprocessor,
                                                   base_image,
                                                   registry,
                                                   needs_deps_installation,
                                                   pod_spec_mutators)
    
    def get_training_deployer(self):
        return Job(namespace=self._namespace, pod_spec_mutators=[gcp.add_gcp_credentials_if_exists])
    
    def get_serving_deployer(self, model_class):
        return Serving(model_class, namespace=self._namespace)

class KubeflowBackend(KubernetesBackend):

    def __init__(self, namespace="kubeflow"):
        super(KubeflowBackend, self).__init__(namespace)
    
    def get_training_deployer(self):
        return Job(namespace=self._namespace)

class KubeflowGKEBackend(GKEBackend):

    def __init__(self, namespace="kubeflow"):
        super(KubeflowGKEBackend, self).__init__(namespace)
    
    def get_training_deployer(self):
        return Job(namespace=self._namespace, pod_spec_mutators=[gcp.add_gcp_credentials_if_exists])

class GCPManagedBackend(BackendInterface):

    def __init__(self, project_id=None, region=None, training_scale_tier=None):
        super(GCPManagedBackend, self).__init__()
        self._project_id = project_id or gcp.guess_project_name()
        self._region = region or 'us-central1'
        self._training_scale_tier =  training_scale_tier or 'BASIC'
    
    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
        # TODO (karthikv2k): Add cloud build as the deafult
        # once https://github.com/kubeflow/fairing/issues/145 is fixed
        if fairing.utils.is_running_in_k8s():
            return ClusterBuilder(preprocessor=preprocessor,
                                  base_image=base_image,
                                  registry=registry,
                                  pod_spec_mutators=pod_spec_mutators)
        elif ml_tasks_utils.is_docker_daemon_exists():
            return DockerBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        else:
            # TODO (karthikv2k): Add more info on how to reolve this issue
            raise RuntimeError("Not able to guess the right builder for this job!")       

    def get_training_deployer(self):
        return GCPJob(self._project_id, self._region, self._training_scale_tier)

    def get_serving_deployer(self, model_class):
        # currently GCP serving deployer doesn't implement deployer interface
        raise NotImplementedError("GCP managed serving is not integrated into high level API yet.")
