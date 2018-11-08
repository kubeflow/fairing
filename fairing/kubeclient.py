from kubernetes import client as kube_client
from kubernetes import watch
from kubernetes import config
from kubernetes.client.rest import ApiException
import os
import json
import time
from fairing.utils import is_running_in_k8s, get_current_k8s_namespace
import logging
logger = logging.getLogger(__name__)
MAX_RETRIES = 100
MAX_REQUEST_TIMEOUT = 30
MAX_SLEEP_SECONDS = 3
MAX_STREAM_BYTES = 1024


class KubeClient(object):

    def __init__(self, kubeconfig="/var/run/kubernetes/config"):
        self.kubeconfig = kubeconfig
        self.load_config()

    def load_config(self):
        """Create kubernetes config from provided kubeconfig or in_cluster
        :return: an api_client
        """
        if not self.kubeconfig or not os.path.isfile(self.kubeconfig):
            config.load_incluster_config()

        else:
            config.load_kube_config(config_file=self.kubeconfig)

    def run(self, svc):
        if is_running_in_k8s():
            svc['namespace'] = get_current_k8s_namespace()
        else:
            svc['namespace'] = svc.get('namespace') or 'default'
        v1 = kube_client.CoreV1Api()
        v1.create_namespaced_config_map(namespace=svc['namespace'], body=svc['configMap'])
        api_response = v1.read_namespaced_config_map(name=svc['configMap']['metadata']['name'],
                                                     namespace=svc['namespace'],
                                                     pretty='true')
        logger.debug("Created configmap '%s'", api_response)
        api_instance = kube_client.CustomObjectsApi()
        group = 'kubeflow.org'  # str | The custom resource's group name
        version = 'v1alpha2'  # str | The custom resource's version
        plural = 'tfjobs'  # str | The custom resource's plural name.
        namespace = svc['namespace']
        body = svc['tfJob']
        api_response = api_instance.create_namespaced_custom_object(group, version, namespace, plural, body)
        logger.debug("Created tfjob '%s'", api_response)

    def load_configmap(self, name):
        v1 = kube_client.CoreV1Api()
        if is_running_in_k8s():
            namespace = get_current_k8s_namespace()
        else:
            namespace = 'default'
        config_map = v1.read_namespaced_config_map(name=name, namespace=namespace)
        return config_map.data

    def cancel(self, name):
        pass

    def logs(self, name, namespace):
        tail = None
        v1 = kube_client.CoreV1Api()
        # Retry to allow starting of pod
        # TODO Use urllib3's retry
        try:
            w = watch.Watch()
            for event in w.stream(v1.list_namespaced_pod, namespace=namespace, field_selector="metadata.name={}".format(name)):
                logger.info("Event: %s %s %s", event['type'], event['object'].metadata.name,  event['object'].status.phase)
                if event['object'].status.phase == 'Pending':
                    continue
                elif event['object'].status.phase == 'Running' and event['object'].status.container_statuses[0].ready:
                    logger.info("Pod started running %s", event['object'].status.container_statuses[0].ready)
                    tail = v1.read_namespaced_pod_log(name, namespace, follow=True, _preload_content=False)
                    break
                elif event['type'] == 'DELETED' or event['object'].status.phase == 'Failed' or event['object'].status.container_statuses[0].state.waiting:
                    logger.error("Failed to launch %s, reason: %s",  event['object'].metadata.name, event['object'].status.container_statuses[0].state.waiting.reason)
                    tail = v1.read_namespaced_pod_log(name, namespace, follow=True, _preload_content=False)
                    break
        except ValueError as v:
            logger.error("error getting status for {} {}".format(name, str(v)))
        except ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))

        if tail:
            try:
                for chunk in tail.stream(MAX_STREAM_BYTES):
                    print(chunk)
            finally:
                tail.release_conn()

    def cleanup(self, name, namespace):
        # "Watch" till the job is finished
        api_instance = kube_client.CustomObjectsApi()
        job_name = name
        group = 'kubeflow.org'  # str | The custom resource's group name
        version = 'v1alpha2'  # str | The custom resource's version
        plural = 'tfjobs'  # str | The custom resource's plural name.
        retries = MAX_RETRIES
        while retries > 0:
            try:
                api_response = api_instance.get_namespaced_custom_object(group, version, namespace, plural, job_name)
                if bool(api_response['status']['conditions'][-1]['status']):
                    break
                retries -= 1
                time.sleep(MAX_SLEEP_SECONDS)
            except ApiException as e:
                logger.error("error getting status for {} {}".format(job_name, str(e)))
                break

        v1 = kube_client.CoreV1Api()
        body = kube_client.V1DeleteOptions()
        v1.delete_namespaced_config_map(name, namespace, body)
