import logging

from kubernetes import client

from fairing.builders.builder import BuilderInterface
from fairing.constants import constants
from fairing.cloud import gcp

logger = logging.getLogger(__name__)


class BaseBuilder(BuilderInterface):
    """A builder using the local Docker client"""

    def __init__(self,
                 registry=None,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 preprocessor=None,
                 dockerfile_path=None):

        self.registry = registry
        if self.registry is None:
            # TODO(r2d4): Add more heuristics here...
            self.registry = 'gcr.io/{}'.format(gcp.guess_project_name())

        self.base_image = base_image
        self.dockerfile_path = dockerfile_path
        self.preprocessor = preprocessor
        self.image_name = None
        self.image_tag = None
        self.docker_client = None

        if self.registry.count("/") == 0:
            self.registry = "{DEFAULT_REGISTRY}/{USER_REPOSITORY}".format(
                DEFAULT_REGISTRY=constants.DEFAULT_REGISTRY, 
                USER_REPOSITORY=self.registry)

    def generate_pod_spec(self):
        """return a V1PodSpec initialized with the proper container"""
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.image_tag,
                command=self.preprocessor.get_command(),
                security_context=client.V1SecurityContext(
                    run_as_user=0,
                ),
                image_pull_policy='Always',
                env=[client.V1EnvVar(
                    name='FAIRING_RUNTIME',
                    value='1',
                )]
            )],
            restart_policy='Never'
        )

    def full_image_name(self, tag):
        image_name = constants.DEFAULT_IMAGE_NAME
        return '{}/{}:{}'.format(self.registry, image_name, tag)

    def build(self):
        """Runs the build"""
        raise NotImplementedError()
