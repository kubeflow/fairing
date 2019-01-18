from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()

import logging
logger = logging.getLogger(__name__)
from pprint import pprint

from kubernetes import client, config, watch
from fairing.utils import is_running_in_k8s

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
        api_instance.create_namespaced_job(namespace, job)
    
    def create_tf_job(self, namespace, job):
        """Create the provided TFJob in the specified namespace"""
        api_instance = client.CustomObjectsApi()
        api_instance.create_namespaced_custom_object(
            TF_JOB_GROUP,
            TF_JOB_VERSION,
            namespace,
            TF_JOB_PLURAL,
            job
        )

    def create_deployment(self, namespace, deployment):
        """Create an ExtensionsV1beta1Deployment in the specified namespace"""
        api_instance = client.ExtensionsV1beta1Api()
        api_instance.create_namespaced_deployment(namespace, deployment)

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

    def log(self, name, namespace, extra_label_selector=None):
        selector = "fairing-job-id={}".format(name)
        if extra_label_selector is not None:
            selector = "{},{}".format(selector, extra_label_selector)

        v1 = client.CoreV1Api()
        # Retry to allow starting of pod
        w = watch.Watch()
        try:
            for event in w.stream(v1.list_namespaced_pod,
                            namespace=namespace,
                            label_selector=selector):
                pod = event['object']
                logger.debug("Event: %s %s %s",
                            event['type'],
                            pod.metadata.name,
                            pod.status.phase)
                if pod.status.phase == 'Pending':
                    logger.warn('Waiting for job to start...')
                    continue
                elif (pod.status.phase == 'Running'
                      and pod.status.container_statuses[0].ready):
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
                    print(chunk.rstrip())
            finally:
                tail.release_conn()
