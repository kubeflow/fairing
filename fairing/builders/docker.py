import shutil
import os
import json
import logging
import sys

from docker import APIClient

from fairing.builders.dockerfile import DockerFile
from fairing.builders.container_image_builder import ContainerImageBuilder
from fairing.utils import get_image_full_name

logger = logging.getLogger(__name__)

class DockerBuilder(ContainerImageBuilder):
    def __init__(self, 
                repository, 
                image_name='fairing-job', 
                image_tag=None, 
                base_image=None, 
                dockerfile_path=None):

        self.repository = repository
        self.image_name = image_name
        if image_tag is None:
            self.image_tag = image_tag

        self.base_image = base_image
        self.dockerfile_path = dockerfile_path
        self.dockerfile = DockerFile()
        self.docker_client = APIClient(version='auto')
      
  
    def execute(self, env):
        full_image_name = get_image_full_name(repository, image_name, image_tag)
        self.dockerfile.write(env, dockerfile=dockerfile, base_image=base_image)
        self.build(full_image_name)
        if publish:
            self.publish(full_image_name)

    def build(self, img, path='.'):
        logger.warn('Building docker image {}...'.format(img))
               
        bld = self.docker_client.build(
            path=path,
            tag=img,
            encoding='utf-8'
        )

        for line in bld:
            self._process_stream(line)

    def publish(self, img):
        logger.warn('Publishing image {}...'.format(img))       

        # TODO: do we need to set tag?
        for line in self.docker_client.push(img, stream=True):
            self._process_stream(line)

    def _process_stream(self, line):
        raw = line.decode('utf-8').strip()
        lns = raw.split('\n')
        for ln in lns:
            # try to decode json
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
