from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from future import standard_library
standard_library.install_aliases()

import shutil
import os
import json
import logging
import sys

from docker import APIClient
from kubernetes import client

from fairing import utils
from .builder import BuilderInterface
from .dockerfile import write_dockerfile

logger = logging.getLogger(__name__)
DEFAULT_IMAGE_NAME = 'fairing-job'

class DockerBuilder(BuilderInterface):
    """A builder using the local Docker client"""

    def __init__(self, 
                repository, 
                image_name=DEFAULT_IMAGE_NAME, 
                image_tag=None, 
                base_image=None, 
                dockerfile_path=None):

        self.repository = repository
        self.image_name = image_name
        self.base_image = base_image
        self.dockerfile_path = dockerfile_path

        if image_tag is None:
            self.image_tag = utils.get_unique_tag()
        else: 
            self.image_tag = image_tag
        self.full_image_name = utils.get_image_full_name(
            self.repository, 
            self.image_name,
            self.image_tag
        )
        self.docker_client = None
      
    def generate_pod_spec(self):
        """return a V1PodSpec initialized with the proper container"""

        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.full_image_name,
            )],
            restart_policy='Never'
        )
        
    def execute(self):
        write_dockerfile(
            dockerfile_path=self.dockerfile_path, 
            base_image=self.base_image)
        self.docker_client = APIClient(version='auto')
        self.build()       
        self.publish()

    def build(self):
        logger.warn('Building docker image {}...'.format(self.full_image_name))
        bld = self.docker_client.build(
            path='.',
            tag=self.full_image_name,
            encoding='utf-8'
        )

        for line in bld:
            self._process_stream(line)

    def publish(self):
        logger.warn('Publishing image {}...'.format(self.full_image_name))       
        for line in self.docker_client.push(self.full_image_name, stream=True):
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
