# Copyright 2019 The Kubeflow Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import uuid
import logging

from kubernetes import client as k8s_client

from kfserving import V1alpha2EndpointSpec
from kfserving import V1alpha2PredictorSpec
from kfserving import V1alpha2TensorflowSpec
from kfserving import V1alpha2ONNXSpec
from kfserving import V1alpha2PyTorchSpec
from kfserving import V1alpha2SKLearnSpec
from kfserving import V1alpha2TensorRTSpec
from kfserving import V1alpha2XGBoostSpec
from kfserving import V1alpha2CustomSpec
from kfserving import V1alpha2InferenceServiceSpec
from kfserving import V1alpha2InferenceService

from kubeflow.fairing.constants import constants
from kubeflow.fairing.deployers.deployer import DeployerInterface
from kubeflow.fairing.kubernetes.manager import KubeManager
from kubeflow.fairing import utils

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class KFServing(DeployerInterface):
    """Serves a prediction endpoint using Kubeflow KFServing."""

    def __init__(self, framework, default_storage_uri=None, canary_storage_uri=None,
                 canary_traffic_percent=0, namespace=None, labels=None, annotations=None,
                 custom_default_container=None, custom_canary_container=None,
                 stream_log=False, cleanup=False):
        """
        :param framework: The framework for the InferenceService, such as Tensorflow,
            XGBoost and ScikitLearn etc.
        :param default_storage_uri: URI pointing to Saved Model assets for default service.
        :param canary_storage_uri: URI pointing to Saved Model assets for canary service.
        :param canary_traffic_percent: The amount of traffic to sent to the canary, defaults to 0.
        :param namespace: The k8s namespace where the InferenceService will be deployed.
        :param labels: Labels for the InferenceService, separate with commas if have more than one.
        :param annotations: Annotations for the InferenceService,
            separate with commas if have more than one.
        :param custom_default_container: A flexible custom default container for arbitrary customer
                                 provided containers.
        :param custom_canary_container: A flexible custom canary container for arbitrary customer
                                 provided containers.
        :param stream_log: Show log or not when InferenceService started, defaults to True.
        :param cleanup: Delete the kfserving or not, defaults to False.
        """
        self.framework = framework
        self.default_storage_uri = default_storage_uri
        self.canary_storage_uri = canary_storage_uri
        self.canary_traffic_percent = canary_traffic_percent
        self.annotations = annotations
        self.set_labels(labels)
        self.cleanup = cleanup
        self.custom_default_container = custom_default_container
        self.custom_canary_container = custom_canary_container
        self.stream_log = stream_log
        self.backend = KubeManager()

        if namespace is None:
            self.namespace = utils.get_default_target_namespace()
        else:
            self.namespace = namespace

        if self.framework != 'custom' and self.default_storage_uri is None:
            raise RuntimeError("The default_storage_uri must be specified for "
                               "{} framework.".format(self.framework))
        if self.framework == 'custom' and self.custom_default_container is None:
            raise RuntimeError("The custom_default_container must be specified "
                               "for custom framework.")

    def set_labels(self, labels):
        """set label for deployed prediction

        :param labels: dictionary of labels {label_name:label_value}

        """
        self.fairing_id = str(uuid.uuid1())
        self.labels = {'fairing-id': self.fairing_id}
        if labels:
            self.labels.update(labels)

    def deploy(self, isvc):  # pylint:disable=arguments-differ,unused-argument
        """deploy kfserving endpoint

        :param isvc: InferenceService for deploying.

        """
        self.created_isvc = self.backend.create_isvc(
            self.namespace, self.generate_isvc())

        if self.stream_log:
            self.get_logs()

        isvc_name = self.created_isvc['metadata']['name']
        logger.info(
            "Deployed the InferenceService {} successfully.".format(isvc_name))

        if self.cleanup:
            logger.warning(
                "Cleaning up InferenceService {}...".format(isvc_name))
            self.backend.delete_isvc(isvc_name, self.namespace)

        return isvc_name

    def generate_isvc(self):
        """ generate InferenceService """

        api_version = constants.KFSERVING_GROUP + '/' + constants.KFSERVING_VERSION
        default_predictor, canary_predictor = None, None

        if self.framework == 'custom':
            default_predictor = self.generate_predictor_spec(
                self.framework, container=self.custom_default_container)
        else:
            default_predictor = self.generate_predictor_spec(
                self.framework, storage_uri=self.default_storage_uri)

        if self.framework != 'custom' and self.canary_storage_uri is not None:
            canary_predictor = self.generate_predictor_spec(
                self.framework, storage_uri=self.canary_storage_uri)
        if self.framework == 'custom' and self.custom_canary_container is not None:
            canary_predictor = self.generate_predictor_spec(
                self.framework, container=self.custom_canary_container)

        if canary_predictor:
            isvc_spec = V1alpha2InferenceServiceSpec(
                default=V1alpha2EndpointSpec(predictor=default_predictor),
                canary=V1alpha2EndpointSpec(predictor=canary_predictor),
                canary_traffic_percent=self.canary_traffic_percent)
        else:
            isvc_spec = V1alpha2InferenceServiceSpec(
                default=V1alpha2EndpointSpec(predictor=default_predictor),
                canary_traffic_percent=self.canary_traffic_percent)

        return V1alpha2InferenceService(api_version=api_version,
                                        kind=constants.KFSERVING_KIND,
                                        metadata=k8s_client.V1ObjectMeta(
                                            generate_name=constants.KFSERVING_DEFAULT_NAME,
                                            namespace=self.namespace),
                                        spec=isvc_spec)


    def generate_predictor_spec(self, framework, storage_uri=None, container=None):
        '''Generate predictor spec according to framework and
           default_storage_uri or custom container.
        '''
        if self.framework == 'tensorflow':
            predictor = V1alpha2PredictorSpec(
                tensorflow=V1alpha2TensorflowSpec(storage_uri=storage_uri))
        elif self.framework == 'onnx':
            predictor = V1alpha2PredictorSpec(
                onnx=V1alpha2ONNXSpec(storage_uri=storage_uri))
        elif self.framework == 'pytorch':
            predictor = V1alpha2PredictorSpec(
                pytorch=V1alpha2PyTorchSpec(storage_uri=storage_uri))
        elif self.framework == 'sklearn':
            predictor = V1alpha2PredictorSpec(
                sklearn=V1alpha2SKLearnSpec(storage_uri=storage_uri))
        elif self.framework == 'tensorrt':
            predictor = V1alpha2PredictorSpec(
                tensorrt=V1alpha2TensorRTSpec(storage_uri=storage_uri))
        elif self.framework == 'xgboost':
            predictor = V1alpha2PredictorSpec(
                xgboost=V1alpha2XGBoostSpec(storage_uri=V1alpha2XGBoostSpec))
        elif self.framework == 'custom':
            predictor = V1alpha2PredictorSpec(
                custom=V1alpha2CustomSpec(container=container))
        else:
            raise RuntimeError("Unsupported framework {}".format(framework))
        return predictor

    def get_logs(self):
        """ get log from prediction pod"""
        name = self.created_isvc['metadata']['name']
        namespace = self.created_isvc['metadata']['namespace']

        self.backend.log(name, namespace, self.labels,
                         container=constants.KFSERVING_CONTAINER_NAME, follow=False)
