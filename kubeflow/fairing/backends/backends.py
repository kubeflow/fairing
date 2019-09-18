import abc
import six
import sys
import logging

from .. import utils
from ..builders.docker.docker import DockerBuilder
from ..builders.cluster import gcs_context
from ..builders.cluster.cluster import ClusterBuilder
from ..builders.cluster import s3_context
from ..builders.cluster import azurestorage_context
from ..builders.append.append import AppendBuilder
from ..deployers.gcp.gcp import GCPJob
from ..deployers.job.job import Job
from ..deployers.serving.serving import Serving
from ..cloud import aws
from ..cloud import azure
from ..cloud import gcp
from ..cloud import docker
from ..ml_tasks import utils as ml_tasks_utils
from ..constants import constants
from ..kubernetes.manager import KubeManager

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BackendInterface(object):

    @abc.abstractmethod
    def get_builder(self, preprocessor, base_image, registry):
        """Creates a builder instance with right config for the given backend"""
        raise NotImplementedError('BackendInterface.get_builder')

    @abc.abstractmethod
    def get_training_deployer(self, pod_spec_mutators=None):
        """Creates a deployer to be used with a training job"""
        raise NotImplementedError('BackendInterface.get_training_deployer')

    @abc.abstractmethod
    def get_serving_deployer(self, model_class):
        """Creates a deployer to be used with a serving job"""
        raise NotImplementedError('BackendInterface.get_serving_deployer')

    def get_base_contanier(self):
        "Returns the approriate base container for the current environment"
        py_version = ".".join([str(x) for x in sys.version_info[0:3]])
        base_image = 'registry.hub.docker.com/library/python:{}'.format(
            py_version)
        return base_image

    def get_docker_registry(self):
        "Returns the approriate docker registry for the current environment"
        return None


class KubernetesBackend(BackendInterface):

    def __init__(self, namespace=None, build_context_source=None):
        if not namespace and not utils.is_running_in_k8s():
            logger.warning("Can't determine namespace automatically. "
                           "Using 'default' namespace but recomend to provide namespace explicitly"
                           ". Using 'default' namespace might result in unable to mount some "
                           "required secrets in cloud backends.")
        self._namespace = namespace or utils.get_default_target_namespace()
        self._build_context_source = build_context_source

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,  # pylint:disable=arguments-differ
                    pod_spec_mutators=None):
        if not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif utils.is_running_in_k8s():
            return ClusterBuilder(preprocessor=preprocessor,
                                  base_image=base_image,
                                  registry=registry,
                                  pod_spec_mutators=pod_spec_mutators,
                                  namespace=self._namespace,
                                  context_source=self._build_context_source)
        elif ml_tasks_utils.is_docker_daemon_exists():
            return DockerBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        else:
            # TODO (karthikv2k): Add more info on how to reolve this issue
            raise RuntimeError(
                "Not able to guess the right builder for this job!")

    def get_training_deployer(self, pod_spec_mutators=None):
        return Job(self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='LoadBalancer', # pylint:disable=arguments-differ
                             pod_spec_mutators=None):
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)


class GKEBackend(KubernetesBackend):

    def __init__(self, namespace=None, build_context_source=None):
        super(GKEBackend, self).__init__(namespace, build_context_source)
        self._build_context_source = gcs_context.GCSContextSource(
            namespace=self._namespace)

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,
                    pod_spec_mutators=None):

        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)

        if not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif (utils.is_running_in_k8s() or
              not ml_tasks_utils.is_docker_daemon_exists()) and \
                KubeManager().secret_exists(constants.GCP_CREDS_SECRET_NAME, self._namespace):
            return ClusterBuilder(preprocessor=preprocessor,
                                  base_image=base_image,
                                  registry=registry,
                                  pod_spec_mutators=pod_spec_mutators,
                                  namespace=self._namespace,
                                  context_source=self._build_context_source)
        elif ml_tasks_utils.is_docker_daemon_exists():
            return DockerBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        else:
            msg = ["Not able to guess the right builder for this job!"]
            if KubeManager().secret_exists(constants.GCP_CREDS_SECRET_NAME, self._namespace):
                msg.append("It seems you don't have permission to list/access secrets in your "
                           "Kubeflow cluster. We need this permission in order to build a docker "
                           "image using Kubeflow cluster. Adding Kubeneters Admin role to the "
                           "service account you are using might solve this issue.")
            if not utils.is_running_in_k8s():
                msg.append(" Also If you are using 'sudo' to access docker in your system you can"
                           " solve this problem by adding your username to the docker group. "
                           "Reference: https://docs.docker.com/install/linux/linux-postinstall/"
                           "#manage-docker-as-a-non-root-user You need to logout and login to "
                           "get change activated.")
            message = " ".join(msg)
            raise RuntimeError(message)

    def get_training_deployer(self, pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
        return Job(namespace=self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='LoadBalancer',
                             pod_spec_mutators=None):
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)

    def get_docker_registry(self):
        return gcp.get_default_docker_registry()


class AWSBackend(KubernetesBackend):

    def __init__(self, namespace=None, build_context_source=None):
        build_context_source = build_context_source or s3_context.S3ContextSource()
        super(AWSBackend, self).__init__(namespace, build_context_source)

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,
                    pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(aws.add_aws_credentials_if_exists)
        if aws.is_ecr_registry(registry):
            pod_spec_mutators.append(aws.add_ecr_config)
            aws.create_ecr_registry(registry, constants.DEFAULT_IMAGE_NAME)
        return super(AWSBackend, self).get_builder(preprocessor,
                                                   base_image,
                                                   registry,
                                                   needs_deps_installation,
                                                   pod_spec_mutators)

    def get_training_deployer(self, pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(aws.add_aws_credentials_if_exists)
        return Job(namespace=self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='ClusterIP', # pylint:disable=arguments-differ
                             pod_spec_mutators=None):
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)

class AzureBackend(KubernetesBackend):

    def __init__(self, namespace=None, build_context_source=None):
        build_context_source = (
            build_context_source or azurestorage_context.StorageContextSource(namespace=namespace)
        )
        super(AzureBackend, self).__init__(namespace, build_context_source)

    def get_builder(self, preprocessor, base_image, registry,
                    needs_deps_installation=True, pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        if not azure.is_acr_registry(registry):
            raise Exception("'{}' is not an Azure Container Registry".format(registry))
        pod_spec_mutators.append(azure.add_acr_config)
        pod_spec_mutators.append(azure.add_azure_files)
        return super(AzureBackend, self).get_builder(preprocessor,
                                                     base_image,
                                                     registry,
                                                     needs_deps_installation,
                                                     pod_spec_mutators)

class KubeflowBackend(KubernetesBackend):

    def __init__(self, namespace=None, build_context_source=None):
        if not namespace and not utils.is_running_in_k8s():
            namespace = "kubeflow"
        super(KubeflowBackend, self).__init__(namespace, build_context_source)


class KubeflowGKEBackend(GKEBackend):

    def __init__(self, namespace=None, build_context_source=None):
        if not namespace and not utils.is_running_in_k8s():
            namespace = "kubeflow"
        super(KubeflowGKEBackend, self).__init__(
            namespace, build_context_source)


class KubeflowAWSBackend(AWSBackend):

    def __init__(self, namespace=None, build_context_source=None): # pylint:disable=useless-super-delegation
        super(KubeflowAWSBackend, self).__init__(
            namespace, build_context_source)


class KubeflowAzureBackend(AzureBackend):

    def __init__(self, namespace=None, build_context_source=None): # pylint:disable=useless-super-delegation
        super(KubeflowAzureBackend, self).__init__(namespace, build_context_source)


class GCPManagedBackend(BackendInterface):

    def __init__(self, project_id=None, region=None, training_scale_tier=None):
        super(GCPManagedBackend, self).__init__()
        self._project_id = project_id or gcp.guess_project_name()
        self._region = region or 'us-central1'
        self._training_scale_tier = training_scale_tier or 'BASIC'

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,  # pylint:disable=arguments-differ
                    pod_spec_mutators=None):
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
        pod_spec_mutators.append(docker.add_docker_credentials_if_exists)
        # TODO (karthikv2k): Add cloud build as the deafult
        # once https://github.com/kubeflow/fairing/issues/145 is fixed
        if not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif utils.is_running_in_k8s():
            return ClusterBuilder(preprocessor=preprocessor,
                                  base_image=base_image,
                                  registry=registry,
                                  pod_spec_mutators=pod_spec_mutators,
                                  context_source=gcs_context.GCSContextSource(
                                      namespace=utils.get_default_target_namespace()))
        elif ml_tasks_utils.is_docker_daemon_exists():
            return DockerBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        else:
            # TODO (karthikv2k): Add more info on how to reolve this issue
            raise RuntimeError(
                "Not able to guess the right builder for this job!")

    def get_training_deployer(self, pod_spec_mutators=None):
        return GCPJob(self._project_id, self._region, self._training_scale_tier)

    def get_serving_deployer(self, model_class, pod_spec_mutators=None): # pylint:disable=arguments-differ
        # currently GCP serving deployer doesn't implement deployer interface
        raise NotImplementedError(
            "GCP managed serving is not integrated into high level API yet.")

    def get_docker_registry(self):
        return gcp.get_default_docker_registry()
