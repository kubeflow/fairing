import uuid
import logging

from kubernetes import client as k8s_client

from ...constants import constants
from ..deployer import DeployerInterface
from ...kubernetes.manager import KubeManager
from ... import utils

logger = logging.getLogger(__name__)


class KFServing(DeployerInterface):
    """
    Serves a prediction endpoint using Kubeflow KFServing.
    Attributes:
        framework: The framework for the kfservice, such as Tensorflow, XGBoost and ScikitLearn etc.
        default_model_uri: URI pointing to Saved Model assets for default service.
        canary_model_uri: URI pointing to Saved Model assets for canary service.
        canary_traffic_percent: The amount of traffic to sent to the canary, defaults to 0.
        namespace: The k8s namespace where the kfservice will be deployed.
        labels: Labels for the kfservice, separate with commas if have more than one.
        annotations: Annotations for the kfservice, separate with commas if have more than one.
        custom_default_spec: A flexible custom default specification for arbitrary customer
                            provided containers.
        custom_canary_spec: A flexible custom canary specification for arbitrary customer
                            provided containers.
        stream_log: Show log or not when kfservice started, defaults to True.
        cleanup: Delete the kfserving or not, defaults to False.
    """

    def __init__(self, framework, default_model_uri=None, canary_model_uri=None,
                 canary_traffic_percent=0, namespace=None, labels=None, annotations=None,
                 custom_default_spec=None, custom_canary_spec=None, stream_log=True,
                 cleanup=False):
        self.framework = framework
        self.default_model_uri = default_model_uri
        self.canary_model_uri = canary_model_uri
        self.canary_traffic_percent = canary_traffic_percent
        self.annotations = annotations
        self.set_labels(labels)
        self.cleanup = cleanup
        self.custom_default_spec = custom_default_spec
        self.custom_canary_spec = custom_canary_spec
        self.stream_log = stream_log
        self.backend = KubeManager()

        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace

    def set_labels(self, labels):
        self.fairing_id = str(uuid.uuid1())
        self.labels = {'fairing-id': self.fairing_id}
        if labels:
            self.labels.update(labels)

    def deploy(self, template_spec): # pylint:disable=arguments-differ,unused-argument
        self.kfservice = self.generate_kfservice()
        self.created_kfserving = self.backend.create_kfserving(
            self.namespace, self.kfservice)
        if self.stream_log:
            self.get_logs()

        kfservice_name = self.created_kfserving['metadata']['name']
        logger.warning(
            "Deployed the kfservice {} successfully.".format(kfservice_name))

        if self.cleanup:
            logger.warning("Cleaning up kfservice {}...".format(kfservice_name))
            self.backend.delete_kfserving(kfservice_name, self.namespace)

        return kfservice_name

    def generate_kfservice(self):

        spec = {}
        spec['default'] = {}
        if self.framework is not 'custom': # pylint:disable=literal-comparison
            if self.default_model_uri is not None:
                spec['default'][self.framework] = {}
                spec['default'][self.framework]['modelUri'] = self.default_model_uri
            else:
                raise RuntimeError(
                    "The default_model_uri must be defined if the framework is not custom.")
        else:
            if self.custom_default_spec is not None:
                # TBD @jinchi Need to validate the custom_default_spec before executing.
                spec['default'][self.framework] = self.custom_default_spec
            else:
                raise RuntimeError(
                    "The custom_default_spec must be defined if the framework is custom.")

        if self.framework != 'custom':
            if self.canary_model_uri is not None:
                spec['canary'] = {}
                spec['canary'][self.framework] = {}
                spec['canary'][self.framework]['modelUri'] = self.canary_model_uri
                spec['canaryTrafficPercent'] = self.canary_traffic_percent
        else:
            if self.custom_default_spec is not None:
                spec['canary'] = {}
                spec['canary'][self.framework] = self.custom_canary_spec
                spec['canaryTrafficPercent'] = self.canary_traffic_percent

        metadata = k8s_client.V1ObjectMeta(
            generate_name=constants.KFSERVING_DEFAULT_NAME,
            namespace=self.namespace,
            labels=self.labels,
            annotations=self.annotations
        )

        kfservice = {}
        kfservice['kind'] = constants.KFSERVING_KIND
        kfservice['apiVersion'] = constants.KFSERVING_GROUP + \
            '/' + constants.KFSERVING_VERSION
        kfservice['metadata'] = metadata
        kfservice['spec'] = spec

        return kfservice

    def get_logs(self):
        name = self.created_kfserving['metadata']['name']
        namespace = self.created_kfserving['metadata']['namespace']

        self.backend.log(name, namespace, self.labels,
                         container=constants.KFSERVING_CONTAINER_NAME, follow=False)
