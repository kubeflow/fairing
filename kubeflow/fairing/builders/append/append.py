from timeit import default_timer as timer
import httplib2
import os
import logging

from containerregistry.client import docker_creds
from containerregistry.client import docker_name
from containerregistry.client.v2_2 import append
from containerregistry.client.v2_2 import docker_image as v2_2_image
from containerregistry.client.v2_2 import docker_session
from containerregistry.transport import transport_pool
from containerregistry.transform.v2_2 import metadata

from kubeflow.fairing.builders.base_builder import BaseBuilder
from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)


class AppendBuilder(BaseBuilder):
    """Builds a docker image by appending a new layer tarball to an existing
    base image. Does not require docker and runs in userspace.

    :param base_image: Base image to use for the build (default: {constants.DEFAULT_BASE_IMAGE})
    :param image_name: image name to use for the new image(default: {constants.DEFAULT_IMAGE_NAME})
    :param preprocessor: Preprocessor{BasePreProcessor} to use to modify inputs
        before sending them to docker build
    :param push: Whether or not to push the image to the registry

    """

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 push=True,
                 preprocessor=None):
        super().__init__(
            registry=registry,
            image_name=image_name,
            base_image=base_image,
            push=push,
            preprocessor=preprocessor,
        )

    def build(self):
        """Will be called when the build needs to start"""
        transport = transport_pool.Http(httplib2.Http)
        src = docker_name.Tag(self.base_image, strict=False)
        logger.warning("Building image using Append builder...")
        start = timer()
        new_img = self._build(transport, src)
        end = timer()
        logger.warning("Image successfully built in {}s.".format(end-start))
        dst = docker_name.Tag(
            self.full_image_name(self.context_hash), strict=False)
        if self.push:
            self.timed_push(transport, src, new_img, dst)
        else:
            # TODO(r2d4):
            # Load image into local daemon. This wouldn't provide any speedup
            # over using the docker daemon directly.
            pass

    def _build(self, transport, src):
        file, hash = self.preprocessor.context_tar_gz()  # pylint:disable=redefined-builtin
        self.context_file, self.context_hash = file, hash
        self.image_tag = self.full_image_name(self.context_hash)
        creds = docker_creds.DefaultKeychain.Resolve(src)
        with v2_2_image.FromRegistry(src, creds, transport) as src_image:
            with open(self.context_file, 'rb') as f:
                new_img = append.Layer(src_image, f.read(), overrides=metadata.Overrides(
                    cmd=self.preprocessor.get_command(),
                    user='0', env={"FAIRING_RUNTIME": "1"}))
        return new_img

    def _push(self, transport, src, img, dst):
        creds = docker_creds.DefaultKeychain.Resolve(dst)
        with docker_session.Push(dst, creds, transport,
                                 mount=[src.as_repository()]) as session:
            logger.warning("Uploading {}".format(self.image_tag))
            session.upload(img)
        os.remove(self.context_file)

    def timed_push(self, transport, src, img, dst):
        """Push image to the registry and log the time spent to the log

        :param transport: the http transport to use for sending requests
        :param src: repo from which to mount blobs
        :param img: the image to be pushed
        :param dst: the fully-qualified name of the tag to push

        """
        logger.warning("Pushing image {}...".format(self.image_tag))
        start = timer()
        self._push(transport, src, img, dst)
        end = timer()
        logger.warning(
            "Pushed image {} in {}s.".format(self.image_tag, end-start))
