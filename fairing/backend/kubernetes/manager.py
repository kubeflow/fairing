from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()

import logging
import yaml
import json
from jinja2 import Template
logger = logging.getLogger(__name__)
from pprint import pprint

from kubernetes import client, config, watch
from kubernetes.client.rest import ApiException
from fairing.utils import is_running_in_k8s

MAX_STREAM_BYTES = 1024
TF_JOB_GROUP = "kubeflow.org"
TF_JOB_KIND = "TFJob"
TF_JOB_PLURAL = "tfjobs"
TF_JOB_VERSION = "v1alpha2"


class DuplicateItemError(Exception):
   """Raised when there are duplicates"""
   pass


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

    def configmap_exists(self, name, namespace):
        """Check if a configmap exists
           TODO: Use a list instead of read call
        """
        try:
            KubeManager.load_configmap(name, namespace)
            return True
        except ApiException as e:
            logger.info("Could not find configmap %s in namespace %s, error %s", name, namespace, e)
        return False

    @staticmethod
    def load_configmap(name, namespace):
        v1 = client.CoreV1Api()
        config_map = v1.read_namespaced_config_map(name=name, namespace=namespace)
        return config_map.data

    def configmap_tf_job_template(self, name, namespace, pod_template_spec, worker_count, ps_count):
        """Parse configmap. Currently this also merges
        in the image, env, volumes, and mounts from pod_template_spec
        Eventually this should do the same as strategic merge-patch.
        However, right now it does a simple append
        """
        container = pod_template_spec.spec.containers[0]
        cmd = container.command
        append_dict = KubeManager.populate_append_dict(container, pod_template_spec)
        config_map = KubeManager.load_configmap(name='tfjob-template', namespace=namespace)
        template = Template(config_map['tfjob-template.yaml'])
        str = template.render(name=name, cmd=cmd,
                              worker_count=worker_count, ps_count=ps_count)
        tf_job = json.loads(json.dumps(yaml.load(str), indent=2))
        spec_list = KubeManager.populate_spec_list(tf_job)
        KubeManager.append_dict_to_specs(spec_list, append_dict)
        return tf_job

    @staticmethod
    def populate_append_dict(container, pod_template_spec):
        append_dict = {}
        append_dict['env'] = [e.to_dict() for e in container.env]
        append_dict['volumeMounts'] = [v.to_dict() for v in container.volumeMounts]
        append_dict['volumes'] = [v.to_dict() for v in pod_template_spec.spec.volumes]
        return append_dict

    @staticmethod
    def populate_spec_list(tf_job):
        spec_list = []
        tf_replica_specs = tf_job['spec']['tfReplicaSpecs']
        worker_tf_pod_spec = tf_replica_specs['Worker']['template']
        spec_list.append(worker_tf_pod_spec)
        chief_tf_pod_spec = tf_replica_specs['Chief']['template']
        spec_list.append(chief_tf_pod_spec)
        if tf_replica_specs['Ps']:
            ps_tf_pod_psec = tf_replica_specs['Ps']['template']
            spec_list.append(ps_tf_pod_psec)
        if tf_replica_specs['Evaluator']:
            evaluator_tf_pod_psec = tf_replica_specs['Evaluator']['template']
            spec_list.append(evaluator_tf_pod_psec)
        return spec_list

    @staticmethod
    def append_dict_to_specs(spec_list, append_dict):
        for spec in spec_list:
            tensorflow_container = [c for c in filter(lambda x: x['name'] == 'tensorflow',
                                       spec['spec']['containers'])][0]
            #TODO: Generalize?
            if 'env' not in tensorflow_container:
                tensorflow_container['env'] = []
            tensorflow_container['env'].extend(append_dict['env'])
            KubeManager._validate_unique_name(tensorflow_container['env'])
            if 'volumeMounts' not in tensorflow_container:
                tensorflow_container['volumeMounts'] = []
            tensorflow_container['volumeMounts'].extend(append_dict['volumeMounts'])
            KubeManager._validate_unique_name(tensorflow_container['volumeMounts'])
            if 'volumes' not in spec['spec']:
                spec['spec']['volumes'] = []
            spec['spec']['volumes'].extend(append_dict['volumes'])
            KubeManager._validate_unique_name(spec['spec']['volumes'])

    @staticmethod
    def _validate_unique_name(item_list):
        names = [x['name'] for x in item_list]
        if len(names) != len(set(names)):
            raise DuplicateItemError("Item_list '%s' has duplicate names '%s'", item_list, names)

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
