from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()


import httplib2
import os
import logging

from kubernetes import client

from fairing import utils
from fairing.builders import BuilderInterface
from fairing.builders.dockerfile import get_command
from fairing.notebook_helper import is_in_notebook, export_notebook_to_tar_gz

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import append
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.transport import transport_pool

logger = logging.getLogger(__name__)

DEFAULT_IMAGE_NAME = 'fairing-job'
DEFAULT_BASE_IMAGE = 'gcr.io/kubeflow-images-public/fairing-base:v0.0.1'

TEMP_TAR_GZ_FILENAME = '.tmp.fairing.layer.tar.gz'
_THREADS = 8

class AppendBuilder(BuilderInterface):
    def __init__(self,
                repository,
                image_name=DEFAULT_IMAGE_NAME,
                base_image=DEFAULT_BASE_IMAGE,
                image_tag=None):
        self.repository = repository
        self.image_name = image_name
        self.base_image = base_image
        self.image_tag = image_tag

    def execute(self):
        """Will be called when the build needs to start"""
        self.append()

    def generate_pod_spec(self):
        """return a V1PodSpec initialized with the proper container"""
        return client.V1PodSpec(
            containers=[client.V1Container(
                name='model',
                image=self.full_image_name(),
                command=get_command().split(" "),
                env= [client.V1EnvVar(
                    name='FAIRING_RUNTIME',
                    value='1',
                )]
            )],
            restart_policy='Never'
        )

    def append(self):
      if is_in_notebook():
          export_notebook_to_tar_gz(TEMP_TAR_GZ_FILENAME)
      else:
        utils.generate_context_tarball(".", TEMP_TAR_GZ_FILENAME)
      transport = transport_pool.Http(httplib2.Http, size=_THREADS)
      src = docker_name.Tag(self.base_image)
      creds = docker_creds.DefaultKeychain.Resolve(src)
      with v2_2_image.FromRegistry(src, creds, transport) as src_image:
        with open(TEMP_TAR_GZ_FILENAME, 'rb') as f:
          new_img = append.Layer(src_image, f.read())
      if self.image_tag is None:
        self.image_tag = new_img.digest().split(":")[1]
      dst = docker_name.Tag(self.full_image_name())
      creds = docker_creds.DefaultKeychain.Resolve(dst)
      with docker_session.Push(dst, creds, transport, threads=_THREADS, mount=[src.as_repository()]) as session:
        session.upload(new_img)
      os.remove(TEMP_TAR_GZ_FILENAME)
      logger.warn("Pushed image {}".format(self.full_image_name()))
    
    def full_image_name(self):
        return '{}/{}:{}'.format(self.repository, self.image_name, self.image_tag)