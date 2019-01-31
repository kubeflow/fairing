from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from timeit import default_timer as timer
import httplib2
import os
import sys
import logging

from kubernetes import client

import fairing
from fairing import utils
from fairing.builders.base_builder import BaseBuilder
from fairing.constants import constants

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import append
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.transport import transport_pool

logger = logging.getLogger(__name__)

class AppendBuilder(BaseBuilder):
    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 image_tag=None,
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
        """Will be called when the build needs to start"""
        transport = transport_pool.Http(httplib2.Http)
        src = docker_name.Tag(self.base_image, strict=False)
        logger.warn("Building image...")
        start = timer()
        new_img = self._build(transport, src)
        end = timer()
        logger.warn("Image successfully built in {}s.".format(end-start))
        self.timed_push(transport, src, new_img)

    def _build(self, transport, src):
        creds = docker_creds.DefaultKeychain.Resolve(src)
        with v2_2_image.FromRegistry(src, creds, transport) as src_image:
            with open(self.preprocessor.context_tar_gz(), 'rb') as f:
                new_img = append.Layer(src_image, f.read())
        return new_img

    def push(self, transport, src, img):
        dst = docker_name.Tag(self.full_image_name(), strict=False)
        creds = docker_creds.DefaultKeychain.Resolve(dst)
        with docker_session.Push(dst, creds, transport, mount=[src.as_repository()]) as session:
            logger.warn("Uploading {}".format(self.full_image_name()))
            session.upload(img)
        os.remove(self.preprocessor.context_tar_gz())

    def timed_push(self, transport, src, img):
        logger.warn("Pushing image...")
        start = timer()
        self.push(transport, src, img)
        end = timer()
        logger.warn("Pushed image {} in {}s.".format(self.full_image_name(),end-start))
