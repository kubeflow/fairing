import logging
import time
import datetime
import sys

import kubernetes.client
from kubernetes.client.rest import ApiException

logger = logging.getLogger('fairing')


class BuildSpecArgument(object):
    def __init__(self, name, value):
        self._name = name
        self._value = value

    def to_dict(self):
        result = {}
        result['name'] = self._name
        result['value'] = self._value
        return result


class BuildSpecTemplate(object):
    def __init__(self, name, arguments):
         self._name = name
         self._arguments = arguments

    def to_dict(self):
        result = {}
        result['name'] = self._name
        result['arguments'] = list(map(lambda x: x.to_dict(), self._arguments))
        return result


class BuildSpec(object):
    def __init__(self, sa_name, template):
        self._sa_name = sa_name
        self._template = template

    def to_dict(self):
        result = {}
        result['serviceAccountName'] = self._sa_name
        result['template'] = self._template.to_dict()
        return result


class Build(object):
    def __init__(self, metadata, spec):
        # TODO: create a knative helper with all those static values
        self._group = 'build.knative.dev'
        self._api_version = 'v1alpha1'
        self._full_api_version = 'build.knative.dev/v1alpha1'
        self._plural = 'builds'
        self._kind = 'Build'

        self._metadata = metadata
        self._spec = spec

        self._api_custom = None
        self._api_v1 = None
        self._get_api_instances()

    def to_dict(self):
        result = {}
        result['apiVersion'] = self._full_api_version
        result['kind'] = self._kind
        # metadata being a base k8s object, it will be sanitize by the API automatically
        # no need to convert to dict ourselves
        result['metadata'] = self._metadata
        result['spec'] = self._spec.to_dict()
        return result

    def create(self):
        try:
            self._api_custom.create_namespaced_custom_object(group=self._group,
                                                           version=self._api_version,
                                                           namespace=self._metadata.namespace,
                                                           plural=self._plural,
                                                           body=self.to_dict(),
                                                           pretty=True)
        except ApiException as e:
            logger.error(
                "Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)

    def create_sync(self):
        self.create()
        self.wait_for_build_completion()

    def wait_for_build_completion(self):
        timeout = 180
        check_start = datetime.datetime.now()
        while True:
            try:
                bld = self._api_custom.get_namespaced_custom_object(self._group,
                                                                self._api_version,
                                                                self._metadata.namespace,
                                                                self._plural,
                                                                self._metadata.name)
            except ApiException as e:
                logger.error(
                    "Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)

            success = self.check_build_succeeded(bld)
            if success:
                logger.error('Build finished successfully.')
                break
            elif success == False:
                logger.error('Build failed, fetching logs...')
                logger.error(self.fetch_build_logs())
                sys.exit(1)

            if (datetime.datetime.now() - check_start).seconds > timeout:
                logger.error('Timeout while waiting for build to finish.')
                break

            time.sleep(3)

              
    def get_build_pod_labels_selector(self):
        return 'build-name={}'.format(self._metadata.name)

    def _get_api_instances(self):
        self._api_custom=kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient())
        self._api_v1=kubernetes.client.CoreV1Api(kubernetes.client.ApiClient())


    def fetch_build_logs(self):
        try:
            pod_list = self._api_v1.list_namespaced_pod(namespace=self._metadata.namespace,
                                                        include_uninitialized=True,
                                                        label_selector=self.get_build_pod_labels_selector())
        except ApiException as e:
            logger.error("Exception when calling CoreV1Api->list_namespaced_pod: %s\n" % e)

        if len(pod_list.items) > 1:
            raise RuntimeError("Failed fetching logs. Found more than one pod matching labels {labels}"
                                .format(self.get_build_pod_labels_selector()))
        elif len(pod_list.items) == 0:
            raise RuntimeError("Failed fetching logs. Couldn't find any pod matching labels {labels}"
                                .format(self.get_build_pod_labels_selector()))
        
        pod = pod_list.items[0]
       
        return self.get_logs(pod)


    def get_logs(self, pod):
        containers_logs = list(map(lambda c: self.get_logs_for_container(pod, c), pod.spec.containers + pod.spec.init_containers))
        
        containers_logs = containers_logs or []
        return '\n'.join(containers_logs)
    

    def get_logs_for_container(self, pod, container):
        container_status = list(filter(lambda s: s.name == container.name, pod.status.container_statuses + pod.status.init_container_statuses))[0]
        if container_status.state.waiting != None:
            return 'Container {name} is still waiting to start.'.format(name=container.name)
        try: 
            logs = self._api_v1.read_namespaced_pod_log(pod.metadata.name, pod.metadata.namespace, container=container.name, pretty=True)
            return logs
        except ApiException as e:
            logger.error("Exception when calling CoreV1Api->read_namespaced_pod_log: %s\n" % e)

    @staticmethod
    def check_build_succeeded(build_object):
        try:
            condition=build_object['status']['conditions'][0]
        except Exception:  # If for some reason the object is malformed, give it some time
            return None

        if condition['state'] == 'Succeeded':
            if condition['status'] == 'False':
                return False
            if condition['status'] == 'True':
                return True
            return None
        return None
