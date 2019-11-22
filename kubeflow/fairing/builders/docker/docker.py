import json
import logging

from docker import APIClient

from kubeflow.fairing.builders.base_builder import BaseBuilder
from kubeflow.fairing.builders import dockerfile
from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)


class DockerBuilder(BaseBuilder):
    """A builder using the local Docker client"""

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 preprocessor=None,
                 push=True,
                 dockerfile_path=None):
        super().__init__(
            registry=registry,
            image_name=image_name,
            push=push,
            base_image=base_image,
            preprocessor=preprocessor,
            dockerfile_path=dockerfile_path)

    def build(self):
        logging.info("Building image using docker")
        self.docker_client = APIClient(version='auto')
        self._build()
        if self.push:
            self.publish()

    def _build(self):
        """build the docker image"""
        docker_command = self.preprocessor.get_command()
        logger.warning("Docker command: {}".format(docker_command))
        if not docker_command:
            logger.warning("Not setting a command for the output docker image.")
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
        logger.warning('Building docker image {}...'.format(self.image_tag))
        with open(context_file, 'rb') as fileobj:
            bld = self.docker_client.build(
                path='.',
                custom_context=True,
                fileobj=fileobj,
                tag=self.image_tag,
                encoding='utf-8'
            )
        for line in bld:
            self._process_stream(line)

    def publish(self):
        """push the docker image to the docker registry"""
        logger.warning('Publishing image {}...'.format(self.image_tag))
        for line in self.docker_client.push(self.image_tag, stream=True):
            self._process_stream(line)

    def _process_stream(self, line):
        """
        Parse the docker command output by line

        :param line:  a line of the command output message

        """
        raw = line.decode('utf-8').strip()
        lns = raw.split('\n')
        for ln in lns:
            try:
                ljson = json.loads(ln)
                if ljson.get('error'):
                    msg = str(ljson.get('error', ljson))
                    logger.error('Build failed: %s', msg)
                    raise Exception('Image build failed: ' + msg)
                else:
                    if ljson.get('stream'):
                        msg = 'Build output: {}'.format(
                            ljson['stream'].strip())
                    elif ljson.get('status'):
                        msg = 'Push output: {} {}'.format(
                            ljson['status'],
                            ljson.get('progress')
                        )
                    elif ljson.get('aux'):
                        msg = 'Push finished: {}'.format(ljson.get('aux'))
                    else:
                        msg = str(ljson)
                    logger.info(msg)

            except json.JSONDecodeError:
                logger.warning('JSON decode error: {}'.format(ln))
