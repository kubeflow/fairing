import logging

import kubernetes.client
from kubernetes.client.rest import ApiException

logger = logging.getLogger('fairing')

class BuildTemplateSpecParameter(object):
    def __init__(self, name=None, description=None, default=None):
        self._name = name
        self._description = description
        self._default = default

    def to_dict(self):
        result = {}
        result['name'] = self._name
        result['description'] = self._description
        result['default'] = self._default
        return result


class BuildTemplateSpecStep(object):
    def __init__(self, name=None, image=None, args=None, volume_mounts=[]):
        self._name = name
        self._image = image
        self._args = args
        self._volume_mounts = volume_mounts

    def to_dict(self):
        result = {}
        result['name'] = self._name
        result['image'] = self._image
        result['args'] = self._args
        # volumeMounts being a base k8s object, it will be sanitize by the API automatically
        # no need to convert to dict ourselves
        result['volumeMounts'] = self._volume_mounts
        return result


class BuildTemplateSpec(object):
    def __init__(self, parameters=[], steps=[], volumes=[]):
        self._parameters = parameters
        self._steps = steps
        self._volumes = volumes

    def to_dict(self):
        result = {}
        result['parameters'] = list(
            map(lambda x: x.to_dict(), self._parameters))
        result['steps'] = list(map(lambda x: x.to_dict(), self._steps))
        # volumes being a base k8s object, it will be sanitize by the API automatically
        # no need to convert to dict ourselves
        result['volumes'] = self._volumes
        return result


class BuildTemplate(object):
    def __init__(self, metadata=None, spec=None):
        self._group = 'build.knative.dev'
        self._api_version = 'v1alpha1'
        self._full_api_version = 'build.knative.dev/v1alpha1'
        self._plural = 'buildtemplates'
        self._kind = 'BuildTemplate'

        self._metadata = metadata
        self._spec = spec

        self._api_instance = self._get_api_instance()

        # TODO: Add versioning to support upgrades to fairing
        #self.version = ...

    def to_dict(self):
        result = {}
        result['apiVersion'] = self._full_api_version
        result['kind'] = self._kind
        # metadata being a base k8s object, it will be sanitize by the API automatically
        # no need to convert to dict ourselves
        result['metadata'] = self._metadata
        result['spec'] = self._spec.to_dict()

        return result

    def validate(self):       
        if not self._metadata:
            raise AssertionError(
                "Metadata for the BuildTemplate must be provided")

        if not self._spec:
            raise AssertionError(
                "BuildTemplateSpec for BuildTemplate must be provided")

    def maybe_create(self):
        self.validate()
        try:
            self._api_instance.get_namespaced_custom_object(
                self._group, self._api_version, self._metadata.namespace, self._plural, self._metadata.name)
        except ApiException as e:
            if e.status == 404:
                logger.debug('BuildTemplate not found, creating...')
                self._create()
            else:
                logger.error(
                    "Exception when calling CustomObjectsApi->get_namespaced_custom_object: %s\n" % e)
        logger.debug('Existing BuildTemplate found, skipping creation...')
        # TODO: Check for version of the build template, if version doesn't match with current fairing version, delete deploy a new one?? or add version in name and have multiple build-templates ready

    def _create(self):
        try:
            self._api_instance.create_namespaced_custom_object(group=self._group,
                                                               version=self._api_version,
                                                               namespace=self._metadata.namespace,
                                                               plural=self._plural,
                                                               body=self.to_dict(),
                                                               pretty=True)
        except ApiException as e:
            logger.error(
                "Exception when calling CustomObjectsApi->create_namespaced_custom_object: %s\n" % e)

    def _get_api_instance(self):
        return kubernetes.client.CustomObjectsApi(kubernetes.client.ApiClient())
