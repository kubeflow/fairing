import logging
import retrying
import yaml

from kubernetes import client, config, watch
from kfserving import KFServingClient

from kubeflow.tfjob import TFJobClient
from kubeflow.pytorchjob import PyTorchJobClient

from kubeflow.fairing.utils import is_running_in_k8s, camel_to_snake
from kubeflow.fairing.constants import constants
from kubeflow.fairing import utils

logger = logging.getLogger(__name__)

MAX_STREAM_BYTES = 1024


class KubeManager(object):
    """Handles communication with Kubernetes' client."""

    def __init__(self, config_file=None, context=None,
                 client_configuration=None, persist_config=True):
        """
        :param config_file: kubeconfig file, defaults to ~/.kube/config. Note that for the case
               that the SDK is running in cluster and you want to operate in another remote
               cluster, user must set config_file to load kube-config file explicitly.
        :param context: kubernetes context
        :param client_configuration: The kubernetes.client.Configuration to set configs to.
        :param persist_config: If True, config file will be updated when changed
        """
        self.config_file = config_file
        self.context = context
        self.client_configuration = client_configuration
        self.persist_config = persist_config
        if config_file or not is_running_in_k8s():
            config.load_kube_config(
                config_file=self.config_file,
                context=self.context,
                client_configuration=self.client_configuration,
                persist_config=self.persist_config)
        else:
            config.load_incluster_config()

    def create_job(self, namespace, job):
        """Creates a V1Job in the specified namespace.

        :param namespace: The resource
        :param job: Job defination as kubernetes
        :returns: object: Created Job.

        """
        api_instance = client.BatchV1Api()
        return api_instance.create_namespaced_job(namespace, job)

    def create_tf_job(self, namespace, tfjob):
        """Create the provided TFJob in the specified namespace.
        The TFJob version is defined in TF_JOB_VERSION in fairing.constants.
        The version TFJob need to be installed before creating the TFJob.

        :param namespace: The custom resource
        :param tfjob: The JSON schema of the Resource to create
        :returns: object: Created TFJob.

        """
        tfjob_client = TFJobClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        try:
            return tfjob_client.create(tfjob, namespace=namespace)
        except client.rest.ApiException:
            raise RuntimeError("Failed to create TFJob. Perhaps the CRD TFJob version "
                               "{} in not installed(If you use different version you can pass it "
                               "as ENV variable called "
                               "`TF_JOB_VERSION`)?".format(constants.TF_JOB_VERSION))

    def delete_tf_job(self, name, namespace):
        """Delete the provided TFJob in the specified namespace.

        :param name: The custom object
        :param namespace: The custom resource
        :returns: object: The deleted TFJob.

        """
        tfjob_client = TFJobClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        return tfjob_client.delete(name, namespace=namespace)


    def create_pytorch_job(self, namespace, pytorchjob):
        """Create the provided PyTorchJob in the specified namespace.
        The PyTorchJob version is defined in PYTORCH_JOB_VERSION in kubeflow.pytorch.constants.
        The version PyTorchJob need to be installed before creating the PyTorchJob.

        :param namespace: The custom resource
        :param pytorchjob: The JSON schema of the Resource to create
        :returns: object: Created TFJob.

        """
        pytorchjob_client = PyTorchJobClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        try:
            return pytorchjob_client.create(pytorchjob, namespace=namespace)
        except client.rest.ApiException:
            raise RuntimeError("Failed to create PyTorchJob. Perhaps the CRD PyTorchJob version "
                               "{} in not installed(If you use different version you can pass it "
                               "as ENV variable called `PYTORCH_JOB_VERSION`)? "
                               .format(constants.PYTORCH_JOB_VERSION))

    def delete_pytorch_job(self, name, namespace):
        """Delete the provided PyTorchJob in the specified namespace.

        :param name: The custom object
        :param namespace: The custom resource
        :returns: object: The deleted PyTorchJob.

        """
        pytorchjob_client = PyTorchJobClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        return pytorchjob_client.delete(name, namespace=namespace)

    def create_deployment(self, namespace, deployment):
        """Create an V1Deployment in the specified namespace.

        :param namespace: The custom resource
        :param deployment: Deployment body to create
        :returns: object: Created V1Deployments.

        """
        api_instance = client.AppsV1Api()
        return api_instance.create_namespaced_deployment(namespace, deployment)

    def create_isvc(self, namespace, isvc):
        """Create the provided InferenceService in the specified namespace.

        :param namespace: The custom resource
        :param InferenceService: The InferenceService body
        :returns: object: Created InferenceService.

        """
        KFServing = KFServingClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        try:
            created_isvc = KFServing.create(isvc, namespace=namespace)
            isvc_name = created_isvc['metadata']['name']
            isvc_namespace = created_isvc['metadata']['namespace']
            KFServing.get(isvc_name, isvc_namespace, watch=True)
            return created_isvc
        except client.rest.ApiException:
            raise RuntimeError("Failed to create InferenceService. Perhaps the CRD "
                               "InferenceService version {} is not installed? "\
                                   .format(constants.KFSERVING_VERSION))

    def delete_isvc(self, name, namespace):
        """Delete the provided InferenceService in the specified namespace.

        :param name: The custom object
        :param namespace: The custom resource
        :returns: object: The deleted InferenceService.

        """
        KFServing = KFServingClient(
            config_file=self.config_file,
            context=self.context,
            client_configuration=self.client_configuration,
            persist_config=self.persist_config)
        return KFServing.delete(name, namespace=namespace)

    def delete_job(self, name, namespace):
        """Delete the specified job and related pods.

        :param name: The job name
        :param namespace: The resource
        :returns: object: the deleted job.

        """
        api_instance = client.BatchV1Api()
        api_instance.delete_namespaced_job(
            name,
            namespace,
            client.V1DeleteOptions())

    def delete_deployment(self, name, namespace):
        """Delete an existing model deployment and relinquish all resources associated.

        :param name: The deployment name
        :param namespace: The custom resource
        :returns: obje   deployment.

        """
        api_instance = client.ExtensionsV1beta1Api()
        api_instance.delete_namespaced_deployment(
            name,
            namespace,
            client.V1DeleteOptions())

    def secret_exists(self, name, namespace):
        """Check if the secret exists in the specified namespace.

        :param name: The secret name
        :param namespace: The custom resource.
        :returns: bool: True if the secret exists, otherwise return False.

        """
        secrets = client.CoreV1Api().list_namespaced_secret(namespace)
        secret_names = [secret.metadata.name for secret in secrets.items]
        return name in secret_names

    def create_secret(self, namespace, secret):
        """Create secret in the specified namespace.

        :param namespace: The custom resource
        :param secret: The secret body
        :returns: object: Created secret.

        """
        api_instance = client.CoreV1Api()
        return api_instance.create_namespaced_secret(namespace, secret)

    def get_service_external_endpoint(self, name, namespace, selectors=None): #pylint:disable=inconsistent-return-statements
        """Get the service external endpoint as http://ip_or_hostname:5000/predict.

        :param name: The sevice name
        :param namespace: The custom resource
        :param selectors: A selector to restrict the list of returned objects by their labels.
        :param Defaults: to everything
        :returns: str: the service external endpoint.

        """
        label_selector_str = ', '.join("{}={}".format(k, v) for (k, v) in selectors.items())
        v1 = client.CoreV1Api()
        w = watch.Watch()
        print("Waiting for prediction endpoint to come up...")
        try:
            for event in w.stream(v1.list_namespaced_service,
                                  namespace=namespace,
                                  label_selector=label_selector_str):
                svc = event['object']
                logger.debug("Event: %s %s",
                             event['type'],
                             event['object'])
                ing = svc.status.load_balancer.ingress
                if ing is not None and len(ing) > 0: #pylint:disable=len-as-condition
                    # temporarily disable hostname. It's causing CI to fail when
                    # run through papermill
                    #url = "http://{}:5000/predict".format(ing[0].ip or ing[0].hostname)
                    url = "http://{}:5000/predict".format(ing[0].ip)
                    return url
        except ValueError as v:
            logger.error("error getting status for {} {}".format(name, str(v)))
        except client.rest.ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))

    @retrying.retry(wait_fixed=1000, stop_max_attempt_number=20)
    def log(self, name, namespace, selectors=None, container='', follow=True):
        """Get log of the specified pod.

        :param name: The pod name
        :param namespace: The custom resource
        :param selectors: A selector to restrict the list of returned objects by their labels.
        :param Defaults: to everything
        :param container: The container for which to stream logs.
        :param if: there is one container in the pod
        :param follow: True or False (Default value = True)
        :returns: str: logs of the specified pod.

        """
        tail = ''
        label_selector_str = ', '.join("{}={}".format(k, v) for (k, v) in selectors.items())
        v1 = client.CoreV1Api()
        # Retry to allow starting of pod
        w = watch.Watch()
        try:
            for event in w.stream(v1.list_namespaced_pod,
                                  namespace=namespace,
                                  label_selector=label_selector_str):
                pod = event['object']
                logger.debug("Event: %s %s %s",
                             event['type'],
                             pod.metadata.name,
                             pod.status.phase)
                if pod.status.phase == 'Pending':
                    logger.warning('Waiting for {} to start...'.format(pod.metadata.name))
                    continue
                elif ((pod.status.phase == 'Running'
                       and pod.status.container_statuses[0].ready)
                      or pod.status.phase == 'Succeeded'):
                    logger.info("Pod started running %s",
                                pod.status.container_statuses[0].ready)
                    tail = v1.read_namespaced_pod_log(pod.metadata.name,
                                                      namespace,
                                                      follow=follow,
                                                      _preload_content=False,
                                                      pretty='pretty',
                                                      container=container)
                    break
                elif (event['type'] == 'DELETED'
                      or pod.status.phase == 'Failed'
                      or pod.status.container_statuses[0].state.waiting):
                    logger.error("Failed to launch %s, reason: %s, message: %s",
                                 pod.metadata.name,
                                 pod.status.container_statuses[0].state.terminated.reason,
                                 pod.status.container_statuses[0].state.terminated.message)
                    tail = v1.read_namespaced_pod_log(pod.metadata.name,
                                                      namespace,
                                                      follow=follow,
                                                      _preload_content=False,
                                                      pretty='pretty',
                                                      container=container)
                    break
        except ValueError as v:
            logger.error("error getting status for {} {}".format(name, str(v)))
        except client.rest.ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))
        if tail:
            try:
                for chunk in tail.stream(MAX_STREAM_BYTES):
                    print(chunk.rstrip().decode('utf8'))
            finally:
                tail.release_conn()


    def apply_namespaced_object(self, spec, mode='create'): #pylint:disable=too-many-branches
        """Run apply on the provided Kubernetes specs.

        :param specs: The YAML specs to apply.
        :param mode: 4 valid modes: create, patch, replace and delete.
        :returns: applied resources.
        """

        if mode not in ['create', 'patch', 'replace', 'delete']:
            raise ValueError("Unknown mode %s, "
                             "valid modes: create, patch, replace and delete." % mode)

        if not isinstance(spec, dict):
            spec = yaml.load(spec)

        try:
            namespace = spec["metadata"]["namespace"]
        except KeyError:
            namespace = utils.get_default_target_namespace()

        kind = spec["kind"]
        kind_snake = camel_to_snake(kind)
        plural = spec["kind"].lower() + "s"

        if mode in ['patch', 'replace', 'delete']:
            try:
                name = spec["metadata"]["name"]
            except Exception:
                raise RuntimeError("Cannot get the name in the spec for the operation %s." % mode)

        if not "/" in spec["apiVersion"]:
            group = None
        else:
            group, version = spec["apiVersion"].split("/", 1)

        if group is None or group.lower() == "apps":
            if group is None:
                api = client.CoreV1Api()
            else:
                api = client.AppsV1Api()
            method_name = mode + "_namespaced_" + kind_snake
            if mode == 'create':
                method_args = [namespace, spec]
            elif mode == 'delete':
                method_args = [name, namespace]
            else:
                method_args = [name, namespace, spec]
        else:
            api = client.CustomObjectsApi()
            method_name = mode + "_namespaced_custom_object"

            if mode == 'create':
                method_args = [group, version, namespace, plural, spec]
            elif mode == 'delete':
                method_args = [group, version, namespace, plural, name, client.V1DeleteOptions()]
            else:
                method_args = [group, version, namespace, plural, name, spec]

        apply_method = getattr(api, method_name)

        try:
            result = apply_method(*method_args)
        except client.rest.ApiException as e:
            raise RuntimeError(
                "Exception when calling %s->%s: %s\n" % api, apply_method, e)

        return result


    def apply_namespaced_objects(self, specs, mode='create'):
        """Run apply on the provided Kubernetes specs.

        :param specs:  A list of strings or dicts providing the YAML specs to apply.
        :param mode: 4 valid modes: create, patch, replace and delete.
        :returns:

        """
        results = []

        for spec in specs:
            result = self.apply_namespaced_object(spec, mode=mode)
            results.append(result)

        return results
