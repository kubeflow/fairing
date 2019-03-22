import logging

import fairing
from fairing.deployers.job.job import Job
from fairing.deployers.serving.serving import Serving
import fairing.utils as utils

logger = logging.getLogger(__name__)


class BaseTask:

    def __init__(self, entry_point, base_docker_image, docker_registry=None, input_files=[]):
        preprocessor = utils.guess_preprocessor(entry_point, input_files=input_files)
        logger.warn("Using preprocessor: {}".format(type(preprocessor)))

        if not docker_registry:
            guessed_docker_registry = utils.guess_docker_registry()
            if not guessed_docker_registry:
                raise RuntimeError(
                    "Not able to guess docker registry, please specify docker_registry explicitly.")
            self.docker_registry = guessed_docker_registry
        else:
            self.docker_registry = docker_registry
        logger.warn("Using docker registry: {}".format(self.docker_registry))

        gussed_builder = utils.guess_builder(needs_deps_installation=True)
        logger.warn("Using builder: {}".format(gussed_builder.__name__))

        self.builder = gussed_builder(preprocessor=preprocessor,
                                      base_image=base_docker_image,
                                      registry=self.docker_registry)

    def _build(self):
        self.builder.build()
        self.pod_spec = self.builder.generate_pod_spec()


class TrainJob(BaseTask):

    def __init__(self, entry_point, base_docker_image, docker_registry=None, input_files=[]):
        super().__init__(entry_point, base_docker_image, docker_registry, input_files)

    def submit(self):
        self._build()
        deployer = Job()
        deployer.deploy(self.pod_spec)


class PredictionEndpoint(BaseTask):

    def __init__(self, model_class, base_docker_image, docker_registry=None, input_files=[]):
        self.model_class = model_class
        super().__init__(model_class, base_docker_image, docker_registry, input_files)

    def create(self):
        self._build()
        deployer = Serving(serving_class=self.model_class.__name__)
        deployer.deploy(self.pod_spec)
        # TODO shoudl return a prediction endpoint client
