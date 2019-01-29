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
import os

from docker import APIClient
from kubernetes import client

from fairing import utils
from fairing.builders import BuilderInterface
from fairing.builders import dockerfile
from fairing.constants import constants
from fairing.notebook import notebook_util

from fairing.cloud import gcp

logger = logging.getLogger(__name__)

class BaseBuilder(BuilderInterface):
    """A builder using the local Docker client"""

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 image_tag=None,
                 preprocessor=None,
                 dockerfile_path=None):
        
        self.registry = registry
        if self.registry is None:
            # TODO(r2d4): Add more heuristics here...
            self.registry = 'gcr.io/{}'.format(gcp.guess_project_name())

        self.image_name = image_name
        self.base_image = base_image
        self.dockerfile_path = dockerfile_path
        self.preprocessor = preprocessor

        self.image_tag = image_tag
        self.docker_client = None

        if self.registry.count("/") is 0:
            self.registry = "{DEFAULT_REGISTRY}/{USER_REPOSITORY}".format(
                DEFAULT_REGISTRY=constants.DEFAULT_REGISTRY, USER_REPOSITORY=self.registry)

    def generate_pod_spec(self):
        """return a V1PodSpec initialized with the proper container"""
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.full_image_name(),
                command=self.preprocessor.get_command(),
                env=[client.V1EnvVar(
                    name='FAIRING_RUNTIME',
                    value='1',
                )]
            )],
            restart_policy='Never'
        )
    
    def full_image_name(self):
        if self.image_tag is not None:
            return self.image_tag
        return '{}/{}:{}'.format(self.registry, self.image_name, self.preprocessor.get_context_hash())

    def build(self):
        raise NotImplementedError()