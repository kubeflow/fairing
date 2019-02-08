from timeit import default_timer as timer
import httplib2
import os
import logging

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
    """Builds a docker image by appending a new layer tarball to an existing
    base image. Does not require docker and runs in userspace.


     Args:
        registry {str} -- Registry to push image to. Required.
                          Example: gcr.io/kubeflow-images (default: {None})
        base_image {str} -- Base image to use for the image build (default:
                          {constants.DEFAULT_BASE_IMAGE})
        preprocessor {BasePreProcessor} -- Preprocessor to use to modify inputs
                          before sending them to docker build
    """
    def __init__(self,
                 registry=None,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 preprocessor=None):
        super().__init__(
            registry=registry,
            base_image=base_image,
            preprocessor=preprocessor,
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
        file, hash = self.preprocessor.context_tar_gz()
        self.context_file, self.context_hash = file, hash
        self.image_tag = self.full_image_name(self.context_hash)
        creds = docker_creds.DefaultKeychain.Resolve(src)
        with v2_2_image.FromRegistry(src, creds, transport) as src_image:
            with open(self.context_file, 'rb') as f:
                new_img = append.Layer(src_image, f.read())
        return new_img

    def push(self, transport, src, img):
        dst = docker_name.Tag(
            self.full_image_name(self.context_hash), strict=False)
        creds = docker_creds.DefaultKeychain.Resolve(dst)
        with docker_session.Push(
             dst, creds, transport, mount=[src.as_repository()]) as session:
            logger.warn("Uploading {}".format(self.image_tag))
            session.upload(img)
        os.remove(self.context_file)

    def timed_push(self, transport, src, img):
        logger.warn("Pushing image {}...".format(self.image_tag))
        start = timer()
        self.push(transport, src, img)
        end = timer()
        logger.warn(
            "Pushed image {} in {}s.".format(self.image_tag, end-start))
