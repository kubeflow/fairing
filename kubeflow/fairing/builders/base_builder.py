import logging

from kubernetes import client

from kubeflow.fairing.builders.builder import BuilderInterface
from kubeflow.fairing.constants import constants
from kubeflow.fairing.cloud import gcp

logger = logging.getLogger(__name__)


class BaseBuilder(BuilderInterface): #pylint:disable=too-many-instance-attributes
    """A builder using the local Docker client"""

    def __init__(self,
                 registry=None,
                 image_name=None,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 push=True,
                 preprocessor=None,
                 dockerfile_path=None):

        self.registry = registry
        self.image_name = image_name
        self.push = push
        if self.registry is None:
            # TODO(r2d4): Add more heuristics here...

            # If no push and no registry provided, use any registry name
            if not self.push:
                self.registry = 'local/fairing-image'
            else:
                self.registry = 'gcr.io/{}'.format(gcp.guess_project_name())

        self.base_image = base_image
        self.dockerfile_path = dockerfile_path
        self.preprocessor = preprocessor
        self.image_tag = None
        self.docker_client = None

    def generate_pod_spec(self):
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.image_tag,
                command=self.preprocessor.get_command(),
                security_context=client.V1SecurityContext(
                    run_as_user=0,
                ),
                env=[client.V1EnvVar(
                    name='FAIRING_RUNTIME',
                    value='1',
                )],
                # Set the directory where the python files are built.
                # TODO(jlewi): Would it be better to set PYTHONPATH?
                working_dir=self.preprocessor.path_prefix,
            )],
        )

    def full_image_name(self, tag):
        """Retrun the full image name

        :param tag:  the new tag for the image

        """
        return '{}/{}:{}'.format(self.registry, self.image_name, tag)

    def build(self):
        """Runs the build"""
        raise NotImplementedError()
