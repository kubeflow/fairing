
import logging

from fairing.builders.dockerfile import DockerFile
from fairing.builders.container_image_builder import ContainerImageBuilder


logger = logging.getLogger(__name__)


class CmBuilder(ContainerImageBuilder):
    def __init__(self):
        self.docker_client = None
        self.dockerfile = DockerFile()

    def execute(self, repository, image_name, image_tag, base_image, dockerfile, publish, env):
        """Takes the source, nbconverts it to code, and creates a configmap out of it
        :param repository:
        :param image_name:
        :param image_tag:
        :param base_image:
        :param dockerfile:
        :param publish:
        :param env:
        :return:
        """
        pass
