from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()

import shutil
import json
import logging
import sys


from docker import APIClient
from kubernetes import client

from fairing import utils
from fairing.builders.base_builder import BaseBuilder
from fairing.builders import dockerfile
from fairing.constants import constants

logger = logging.getLogger(__name__)

class DockerBuilder(BaseBuilder):
    """A builder using the local Docker client"""

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 image_tag=None,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 preprocessor=None,
                 dockerfile_path=None):
                    super().__init__(
                        registry=registry,
                        image_name=image_name,
                        base_image=base_image,
                        preprocessor=preprocessor,
                        image_tag=image_tag
                    )

    def build(self):
        self.docker_client = APIClient(version='auto')
        self._build()
        self.publish()

    def _build(self):
        dockerfile_path = dockerfile.write_dockerfile(
            dockerfile_path=self.dockerfile_path,
            base_image=self.base_image)
        self.preprocessor.output_map[dockerfile_path] = 'Dockerfile'
        logger.warn('Building docker image {}...'.format(self.full_image_name()))
        with open(self.preprocessor.context_tar_gz(), 'rb') as fileobj:
            bld = self.docker_client.build(
                path='.',
                custom_context=True,
                fileobj=fileobj,
                tag=self.full_image_name(),
                encoding='utf-8'
            )
        for line in bld:
            self._process_stream(line)

    def publish(self):
        logger.warn('Publishing image {}...'.format(self.full_image_name()))       
        for line in self.docker_client.push(self.full_image_name(), stream=True):
            self._process_stream(line)

    def _process_stream(self, line):
        raw = line.decode('utf-8').strip()
        lns = raw.split('\n')
        for ln in lns:
            try:
                ljson = json.loads(ln)
                if ljson.get('error'):
                    msg = str(ljson.get('error', ljson))
                    logger.error('Build failed: ' + msg)
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
