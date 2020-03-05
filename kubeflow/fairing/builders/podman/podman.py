import json
import logging

import os
#from podman import Client

from kubeflow.fairing.builders.base_builder import BaseBuilder
from kubeflow.fairing.builders import dockerfile
from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)


class PodmanBuilder(BaseBuilder):
    """A builder using the local Podman"""

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 preprocessor=None,
                 push=True,
                 dockerfile_path=None,
                 tls_verify=False):
        super().__init__(
            registry=registry,
            image_name=image_name,
            push=push,
            base_image=base_image,
            preprocessor=preprocessor,
            dockerfile_path=dockerfile_path)
        self.tls_verify = tls_verify

    def build(self):
        logging.info("Building image using podman")
        #self.podman_client = Client()
        self._build()
        if self.push:
            self.publish()

    def _build(self):
        """
        build the podman image
        see https://github.com/containers/libpod/blob/master/docs/source/markdown/podman-build.1.md for detail
        """
        docker_command = self.preprocessor.get_command()
        logger.warning("Podman command: {}".format(docker_command))
        if not docker_command:
            logger.warning("Not setting a command for the podman image.")
        install_reqs_before_copy = self.preprocessor.is_requirements_txt_file_present()
        if self.dockerfile_path:
            dockerfile_path = self.dockerfile_path
        else:
            dockerfile_path = dockerfile.write_dockerfile(
                docker_command=docker_command,
                path_prefix=self.preprocessor.path_prefix,
                base_image=self.base_image,
                install_reqs_before_copy=install_reqs_before_copy)
        self.preprocessor.output_map[dockerfile_path] = 'Dockerfile'
        context_file, context_hash = self.preprocessor.context_tar_gz()
        self.image_tag = self.full_image_name(context_hash)
        logger.warning('Building podman image {}...'.format(self.image_tag))

        # Due to this issue, instead of using 'podman_client.images.build', call command line to build
        # https://github.com/containers/python-podman/issues/51
        cmd_build = 'podman build -t {} - < {}'.format(self.image_tag, context_file)
        build_return = os.system(cmd_build)
        if build_return != 0:
            raise Exception('Image build failed')

    def publish(self):
        """
        push the podman image to registry
        see https://github.com/containers/libpod/blob/master/docs/source/markdown/podman-push.1.md for detail
        """
        logger.warning('Publishing image {}...'.format(self.image_tag))

        # Due to this issue, instead of using 'podman_client.image.push', call command line to push
        # https://github.com/containers/python-podman/issues/77
        cmd_push = 'podman push {} --tls-verify={}'.format(self.image_tag, str(self.tls_verify).lower())
        push_return = os.system(cmd_push)
        if push_return != 0:
            raise Exception('Image push failed')