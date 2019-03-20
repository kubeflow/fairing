from kubernetes import client, config, watch
from fairing.utils import is_running_in_k8s

import logging
logger = logging.getLogger(__name__)

MAX_STREAM_BYTES = 1024
TF_JOB_GROUP = "kubeflow.org"
TF_JOB_KIND = "TFJob"
TF_JOB_PLURAL = "tfjobs"
TF_JOB_VERSION = "v1beta1"


class KubeManager(object):
    """Handles communication with Kubernetes' client."""

    def __init__(self):
        if is_running_in_k8s():
            config.load_incluster_config()
        else:
            config.load_kube_config()

    def create_job(self, namespace, job):
        """Creates a V1Job in the specified namespace"""
        api_instance = client.BatchV1Api()
        return api_instance.create_namespaced_job(namespace, job)

    def create_tf_job(self, namespace, job):
        """Create the provided TFJob in the specified namespace"""
        api_instance = client.CustomObjectsApi()
        return api_instance.create_namespaced_custom_object(
            TF_JOB_GROUP,
            TF_JOB_VERSION,
            namespace,
            TF_JOB_PLURAL,
            job
        )

    def create_deployment(self, namespace, deployment):
        """Create an V1Deployment in the specified namespace"""
        api_instance = client.AppsV1Api()
        return api_instance.create_namespaced_deployment(namespace, deployment)

    def delete_job(self, name, namespace):
        """Delete the specified job"""
        api_instance = client.BatchV1Api()
        api_instance.delete_namespaced_job(
            name,
            namespace,
            client.V1DeleteOptions())

    def delete_deployment(self, name, namespace):
        api_instance = client.ExtensionsV1beta1Api()
        api_instance.delete_namespaced_deployment(
            name,
            namespace,
            client.V1DeleteOptions())

    def secret_exists(self, name, namespace):
        secrets = client.CoreV1Api().list_namespaced_secret(namespace)
        secret_names = [secret.metadata.name for secret in secrets.items]
        return name in secret_names

    def add_credentials_to_pod_spec(self, pod_spec):
        # TODO: Extract config options into a global config set, in order to
        # enable platform-specific options.

        # Set appropriate secrets and volumes to enable kubeflow-user service
        # account.
        env_var = client.V1EnvVar(
            name='GOOGLE_APPLICATION_CREDENTIALS',
            value='/etc/secrets/user-gcp-sa.json')
        if pod_spec.containers[0].env:
            pod_spec.containers[0].env.append(env_var)
        else:
            pod_spec.containers[0].env = [env_var]

        volume_mount = client.V1VolumeMount(
            name='user-gcp-sa', mount_path='/etc/secrets', read_only=True)
        if pod_spec.containers[0].volume_mounts:
            pod_spec.containers[0].volume_mounts.append(volume_mount)
        else:
            pod_spec.containers[0].volume_mounts = [volume_mount]

        volume = client.V1Volume(
            name='user-gcp-sa',
            secret=client.V1SecretVolumeSource(secret_name='user-gcp-sa'))
        if pod_spec.volumes:
            pod_spec.volumes.append(volume)
        else:
            pod_spec.volumes = [volume]

    def watch_service_for_external_ip(self, name, namespace, selectors=None):
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
                if ing is not None and len(ing) > 0:
                    print("Prediction endpoint: http://{}:5000/predict".format(ing[0].ip))
        except ValueError as v:
            logger.error("error getting status for {} {}".format(name, str(v)))
        except client.rest.ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))
                                  
    def log(self, name, namespace, selectors=None):
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
                    logger.warn('Waiting for {} to start...'.format(pod.metadata.name))
                    continue
                elif ((pod.status.phase == 'Running'
                      and pod.status.container_statuses[0].ready)
                      or pod.status.phase == 'Succeeded'):
                    logger.info("Pod started running %s",
                                pod.status.container_statuses[0].ready)
                    tail = v1.read_namespaced_pod_log(pod.metadata.name,
                                                      namespace,
                                                      follow=True,
                                                      _preload_content=False,
                                                      pretty='pretty')
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
                                                      follow=True,
                                                      _preload_content=False,
                                                      pretty='pretty')
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
