import logging

from kubernetes import client, config, watch

logger = logging.getLogger(__name__)

class KubeManager(object):
    """Handles commonucation with Kubernetes' client."""

    def __init__(self):
         config.load_kube_config()

    def create_job(self, namespace, job):
        """Creates a V1Job in the specified namespace"""
        api_instance = client.BatchV1Api()
        api_instance.create_namespaced_job(namespace, job)
    
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

    def log(self, name, namespace):
        v1 = client.CoreV1Api()
        # Retry to allow starting of pod
        w = watch.Watch()
        try:
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
        except client.rest.ApiException as e:
            logger.error("error getting status for {} {}".format(name, str(e)))
        if tail:
            try:
                for chunk in tail.stream(MAX_STREAM_BYTES):
                    print(chunk)
            finally:
                tail.release_conn()