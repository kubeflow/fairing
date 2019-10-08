from kubernetes import client, config, watch
from kubeflow.fairing.utils import is_running_in_k8s
from kubeflow.fairing.constants import constants

import logging
logger = logging.getLogger(__name__)

MAX_STREAM_BYTES = 1024


class KubeManager(object):
    """Handles communication with Kubernetes' client."""

    def __init__(self):
        if is_running_in_k8s():
            config.load_incluster_config()
        else:
            config.load_kube_config()

    def create_job(self, namespace, job):
        """Creates a V1Job in the specified namespace.

        :param namespace: The resource
        :param job: Job defination as kubernetes
        :returns: object: Created Job.

        """
        api_instance = client.BatchV1Api()
        return api_instance.create_namespaced_job(namespace, job)

    def create_tf_job(self, namespace, job):
        """Create the provided TFJob in the specified namespace.
        The TFJob version is defined in TF_JOB_VERSION in fairing.constants.
        The version TFJob need to be installed before creating the TFJob.

        :param namespace: The custom resource
        :param job: The JSON schema of the Resource to create
        :returns: object: Created TFJob.

        """
        api_instance = client.CustomObjectsApi()
        try:
            return api_instance.create_namespaced_custom_object(
                constants.TF_JOB_GROUP,
                constants.TF_JOB_VERSION,
                namespace,
                constants.TF_JOB_PLURAL,
                job
            )
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
        api_instance = client.CustomObjectsApi()
        return api_instance.delete_namespaced_custom_object(
            constants.TF_JOB_GROUP,
            constants.TF_JOB_VERSION,
            namespace,
            constants.TF_JOB_PLURAL,
            name,
            client.V1DeleteOptions())

    def create_deployment(self, namespace, deployment):
        """Create an V1Deployment in the specified namespace.

        :param namespace: The custom resource
        :param deployment: Deployment body to create
        :returns: object: Created V1Deployments.

        """
        api_instance = client.AppsV1Api()
        return api_instance.create_namespaced_deployment(namespace, deployment)

    def create_kfserving(self, namespace, kfservice):
        """Create the provided KFServing in the specified namespace.

        :param namespace: The custom resource
        :param kfservice: The kfservice body
        :returns: object: Created KFService.

        """
        api_instance = client.CustomObjectsApi()
        try:
            return api_instance.create_namespaced_custom_object(
                constants.KFSERVING_GROUP,
                constants.KFSERVING_VERSION,
                namespace,
                constants.KFSERVING_PLURAL,
                kfservice)
        except client.rest.ApiException:
            raise RuntimeError("Failed to create KFService. Perhaps the CRD KFServing version "
                               "{} is not installed?".format(constants.KFSERVING_VERSION))

    def delete_kfserving(self, name, namespace):
        """Delete the provided KFServing in the specified namespace.

        :param name: The custom object
        :param namespace: The custom resource
        :returns: object: The deleted kfservice.

        """
        api_instance = client.CustomObjectsApi()
        return api_instance.delete_namespaced_custom_object(
            constants.KFSERVING_GROUP,
            constants.KFSERVING_VERSION,
            namespace,
            constants.KFSERVING_PLURAL,
            name,
            client.V1DeleteOptions())

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
                    url = "http://{}:5000/predict".format(ing[0].ip or ing[0].hostname)
                    return url
        except ValueError as v:
            logger.error("error getting status for {} {}".format(name, str(v)))
        except client.rest.ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))

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
