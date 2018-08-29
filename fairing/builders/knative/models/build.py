import logging

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

        self._api_instance = self._get_api_instance()

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
            self._api_instance.create_namespaced_custom_object(group=self._group,
                                                           version=self._api_version,
                                                           namespace=self._metadata.namespace,
                                                           plural=self._plural,
                                                           body=self.to_dict(),
                                                           pretty=True)
        except ApiException as e:
            print(
                "Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)

    def _get_api_instance(self):
        return kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient())
