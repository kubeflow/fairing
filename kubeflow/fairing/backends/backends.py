import abc
import six
import sys
import logging

from kubeflow.fairing import utils
from kubeflow.fairing.builders.docker.docker import DockerBuilder
from kubeflow.fairing.builders.cluster import gcs_context
from kubeflow.fairing.builders.cluster.cluster import ClusterBuilder
from kubeflow.fairing.builders.cluster import s3_context
from kubeflow.fairing.builders.cluster import azurestorage_context
from kubeflow.fairing.builders.append.append import AppendBuilder
from kubeflow.fairing.deployers.gcp.gcp import GCPJob
from kubeflow.fairing.deployers.job.job import Job
from kubeflow.fairing.deployers.serving.serving import Serving
from kubeflow.fairing.cloud import aws
from kubeflow.fairing.cloud import azure
from kubeflow.fairing.cloud import gcp
from kubeflow.fairing.cloud import docker
from kubeflow.fairing.ml_tasks import utils as ml_tasks_utils
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.manager import KubeManager

logger = logging.getLogger(__name__)


@six.add_metaclass(abc.ABCMeta)
class BackendInterface(object):
    """ Backend interface.
    Creating a builder instance or a deployer to be used with a traing job or a serving job
    for the given backend.
    And get the approriate base container or docker registry for the current environment.
    """

    @abc.abstractmethod
    def get_builder(self, preprocessor, base_image, registry):
        """Creates a builder instance with right config for the given backend

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this builder
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :raises NotImplementedError: not implemented exception

        """

        raise NotImplementedError('BackendInterface.get_builder')

    @abc.abstractmethod
    def get_training_deployer(self, pod_spec_mutators=None):
        """Creates a deployer to be used with a training job

        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value = None)
        :raises NotImplementedError: not implemented exception

        """

        raise NotImplementedError('BackendInterface.get_training_deployer')

    @abc.abstractmethod
    def get_serving_deployer(self, model_class):
        """Creates a deployer to be used with a serving job

        :param model_class: the name of the class that holds the predict function.
        :raises NotImplementedError: not implemented exception

        """

        raise NotImplementedError('BackendInterface.get_serving_deployer')

    def get_base_contanier(self):
        """Returns the approriate base container for the current environment

        :returns: base image

        """

        py_version = ".".join([str(x) for x in sys.version_info[0:3]])
        base_image = 'registry.hub.docker.com/library/python:{}'.format(
            py_version)
        return base_image

    def get_docker_registry(self):
        """Returns the approriate docker registry for the current environment

        :returns: None

        """

        return None


class KubernetesBackend(BackendInterface):
    """ Use to create a builder instance and create a deployer to be used with a traing job or
    a serving job for the Kubernetes.
    """
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
        """Creates a builder instance with right config for the given Kubernetes

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this job
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :param needs_deps_installation:  need depends on installation(Default value = True)
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value =None)

        """
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
        """Creates a deployer to be used with a training job for the Kubernetes

        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)
        :returns: job for handle all the k8s' template building for a training

        """
        return Job(self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='ClusterIP', # pylint:disable=arguments-differ
                             pod_spec_mutators=None):
        """Creates a deployer to be used with a serving job for the Kubernetes

        :param model_class: the name of the class that holds the predict function.
        :param service_type: service type (Default value = 'ClusterIP')
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)

        """
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)


class GKEBackend(KubernetesBackend):
    """ Use to create a builder instance and create a deployer to be used with a traing job
    or a serving job for the GKE backend.
    And get the approriate docker registry for GKE.
    """

    def __init__(self, namespace=None, build_context_source=None):
        super(GKEBackend, self).__init__(namespace, build_context_source)
        self._build_context_source = gcs_context.GCSContextSource(
            namespace=self._namespace)

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,
                    pod_spec_mutators=None):
        """Creates a builder instance with right config for GKE

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this job
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :param needs_deps_installation:  need depends on installation(Default value = True)
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value =None)

        """

        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)

        if not needs_deps_installation:
            return AppendBuilder(preprocessor=preprocessor,
                                 base_image=base_image,
                                 registry=registry)
        elif (utils.is_running_in_k8s() or
              not ml_tasks_utils.is_docker_daemon_exists()):
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
        """Creates a deployer to be used with a training job for GKE

        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)
        :returns: job for handle all the k8s' template building for a training

        """
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(gcp.add_gcp_credentials_if_exists)
        return Job(namespace=self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='ClusterIP',
                             pod_spec_mutators=None):
        """Creates a deployer to be used with a serving job for GKE

        :param model_class: the name of the class that holds the predict function.
        :param service_type: service type (Default value = 'ClusterIP')
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)

        """
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)

    def get_docker_registry(self):
        """Returns the approriate docker registry for GKE

        :returns: docker registry

        """
        return gcp.get_default_docker_registry()


class AWSBackend(KubernetesBackend):
    """ Use to create a builder instance and create a deployer to be used with a traing job
    or a serving job for the AWS backend.
    """

    def __init__(self, namespace=None, build_context_source=None):
        build_context_source = build_context_source or s3_context.S3ContextSource()
        super(AWSBackend, self).__init__(namespace, build_context_source)

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,
                    pod_spec_mutators=None):
        """Creates a builder instance with right config for AWS

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this job
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :param needs_deps_installation:  need depends on installation(Default value = True)
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value =None)

        """
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
        """Creates a deployer to be used with a training job for AWS

        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)
        :returns: job for handle all the k8s' template building for a training

        """
        pod_spec_mutators = pod_spec_mutators or []
        pod_spec_mutators.append(aws.add_aws_credentials_if_exists)
        return Job(namespace=self._namespace, pod_spec_mutators=pod_spec_mutators)

    def get_serving_deployer(self, model_class, service_type='ClusterIP', # pylint:disable=arguments-differ
                             pod_spec_mutators=None):
        """Creates a deployer to be used with a serving job for AWS

        :param model_class: the name of the class that holds the predict function.
        :param service_type: service type (Default value = 'ClusterIP')
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)

        """
        return Serving(model_class, namespace=self._namespace, service_type=service_type,
                       pod_spec_mutators=pod_spec_mutators)

class AzureBackend(KubernetesBackend):
    """ Use to create a builder instance and create a deployer to be used with a traing job or
    a serving job for the Azure backend.
    """
    def __init__(self, namespace=None, build_context_source=None):
        build_context_source = (
            build_context_source or azurestorage_context.StorageContextSource(namespace=namespace)
        )
        super(AzureBackend, self).__init__(namespace, build_context_source)

    def get_builder(self, preprocessor, base_image, registry,
                    needs_deps_installation=True, pod_spec_mutators=None):
        """Creates a builder instance with right config for Azure

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this job
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :param needs_deps_installation:  need depends on installation(Default value = True)
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value =None)

        """
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
    """Kubeflow backend refer to KubernetesBackend """

    def __init__(self, namespace=None, build_context_source=None):
        if not namespace and not utils.is_running_in_k8s():
            namespace = "kubeflow"
        super(KubeflowBackend, self).__init__(namespace, build_context_source)


class KubeflowGKEBackend(GKEBackend):
    """Kubeflow for GKE backend refer to GKEBackend """

    def __init__(self, namespace=None, build_context_source=None):
        if not namespace and not utils.is_running_in_k8s():
            namespace = "kubeflow"
        super(KubeflowGKEBackend, self).__init__(
            namespace, build_context_source)


class KubeflowAWSBackend(AWSBackend):
    """Kubeflow for AWS backend refer to AWSBackend """

    def __init__(self, namespace=None, build_context_source=None): # pylint:disable=useless-super-delegation
        super(KubeflowAWSBackend, self).__init__(
            namespace, build_context_source)


class KubeflowAzureBackend(AzureBackend):
    """Kubeflow for Azure backend refer to AzureBackend """

    def __init__(self, namespace=None, build_context_source=None): # pylint:disable=useless-super-delegation
        super(KubeflowAzureBackend, self).__init__(namespace, build_context_source)


class GCPManagedBackend(BackendInterface):
    """ Use to create a builder instance and create a deployer to be used with a traing job
    or a serving job for the GCP.
    """
    def __init__(self, project_id=None, region=None, training_scale_tier=None):
        super(GCPManagedBackend, self).__init__()
        self._project_id = project_id or gcp.guess_project_name()
        self._region = region or 'us-central1'
        self._training_scale_tier = training_scale_tier or 'BASIC'

    def get_builder(self, preprocessor, base_image, registry, needs_deps_installation=True,  # pylint:disable=arguments-differ
                    pod_spec_mutators=None):
        """Creates a builder instance with right config for GCP

        :param preprocessor: Preprocessor to use to modify inputs
        :param base_image: Base image to use for this job
        :param registry: Registry to push image to. Example: gcr.io/kubeflow-images
        :param needs_deps_installation:  need depends on installation(Default value = True)
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
                                  e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
                                  This can used to set things like volumes and security context.
                                  (Default value =None)

        """
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
        """Creates a deployer to be used with a training job for GCP

        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)
        :returns: job for handle all the k8s' template building for a training

        """
        return GCPJob(self._project_id, self._region, self._training_scale_tier)

    def get_serving_deployer(self, model_class, pod_spec_mutators=None): # pylint:disable=arguments-differ
        """Creates a deployer to be used with a serving job for GCP

        :param model_class: the name of the class that holds the predict function.
        :param service_type: service type (Default value = 'ClusterIP')
        :param pod_spec_mutators: list of functions that is used to mutate the podsspec.
            (Default value = None)

        """
        # currently GCP serving deployer doesn't implement deployer interface
        raise NotImplementedError(
            "GCP managed serving is not integrated into high level API yet.")

    def get_docker_registry(self):
        """Returns the approriate docker registry for GCP

        :returns: docker registry

        """
        return gcp.get_default_docker_registry()
