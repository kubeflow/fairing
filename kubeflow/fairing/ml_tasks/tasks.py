import logging
import json
import numpy as np
from ..backends import KubernetesBackend
from .utils import guess_preprocessor

import requests

logger = logging.getLogger(__name__)


class BaseTask:
    """
    Base class for handling high level ML tasks.
    args:
        entry_point: An object or reference to the source code that has to be deployed.
        base_docker_image: Name of the base docker image that should be used as a base image
            when building a new docker image as part of an ML task deployment.
        docker_registry: Docker registry to store output docker images.
        input_files: list of files that needs to be packaged along with the entry point.
            E.g. local python modules, trained model weigths, etc.
    """

    def __init__(self, entry_point, base_docker_image=None, docker_registry=None,
                 input_files=None, backend=None, pod_spec_mutators=None):
        self._backend = backend or KubernetesBackend()
        self._pod_spec_mutators = pod_spec_mutators or []
        input_files = input_files or []
        output_map = {}

        preprocessor = guess_preprocessor(entry_point,
                                          input_files=input_files,
                                          output_map=output_map)
        logger.debug("Using preprocessor: {}".format(type(preprocessor)))

        self.docker_registry = docker_registry or backend.get_docker_registry()
        if not self.docker_registry:
            raise RuntimeError("Not able find a default docker registry."
                               " Please provide 'docker_registry' argument explicitly."
                               " Docker registry is used to store the output docker images"
                               " that are executed in the remote cluster.")
        if not docker_registry:
            logger.warning("Using default docker registry: {}".format(
                self.docker_registry))

        self.base_docker_image = base_docker_image or backend.get_base_contanier()
        if not self.base_docker_image:
            raise RuntimeError("Not able find a default base docker image."
                               " Please provide 'base_docker_image' argument explicitly."
                               " Base docker image is used to build the output docker images"
                               " that are executed in the remote cluster.")
        if not base_docker_image:
            logger.warning("Using default base docker image: {}".format(
                self.base_docker_image))

        needs_deps_installation = "requirements.txt" in input_files
        self.builder = self._backend.get_builder(preprocessor=preprocessor,
                                                 base_image=self.base_docker_image,
                                                 registry=self.docker_registry,
                                                 needs_deps_installation=needs_deps_installation)
        logger.warning("Using builder: {}".format(type(self.builder)))

    def _build(self):
        logging.info("Building the docker image.")
        self.builder.build()
        self.pod_spec = self.builder.generate_pod_spec()


class TrainJob(BaseTask):

    def __init__(self, entry_point, base_docker_image=None, docker_registry=None,  # pylint:disable=useless-super-delegation
                 input_files=None, backend=None, pod_spec_mutators=None):
        super().__init__(entry_point, base_docker_image, docker_registry,
                         input_files, backend, pod_spec_mutators)

    def submit(self):
        self._build()
        deployer = self._backend.get_training_deployer(
            pod_spec_mutators=self._pod_spec_mutators)
        return deployer.deploy(self.pod_spec)


class PredictionEndpoint(BaseTask):

    def __init__(self, model_class, base_docker_image=None, docker_registry=None, input_files=None,
                 backend=None, service_type='LoadBalancer', pod_spec_mutators=None):
        self.model_class = model_class
        self.service_type = service_type
        super().__init__(model_class, base_docker_image, docker_registry,
                         input_files, backend, pod_spec_mutators)

    def create(self):
        self._build()
        logging.info("Deploying the endpoint.")
        self._deployer = self._backend.get_serving_deployer(
            self.model_class.__name__,
            service_type=self.service_type,
            pod_spec_mutators=self._pod_spec_mutators)
        self.url = self._deployer.deploy(self.pod_spec)
        logger.warning("Prediction endpoint: {}".format(self.url))

    def predict_nparray(self, data, feature_names=None):
        pdata = {
            "data": {
                "names": feature_names,
                "tensor": {
                    "shape": np.asarray(data.shape).tolist(),
                    "values": data.flatten().tolist(),
                },
            }
        }
        serialized_data = json.dumps(pdata)
        r = requests.post(self.url, data={'json': serialized_data})
        return json.loads(r.text)

    def delete(self):
        logging.info("Deleting the endpoint.")
        self._deployer.delete()
