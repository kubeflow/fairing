from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import time
import os
import logging


from kubernetes import client

from fairing.builders.base_builder import BaseBuilder
from fairing.builders import dockerfile
from fairing.constants import constants
from fairing.kubernetes.manager import KubeManager
from fairing.kubernetes import client
from fairing.builders.cluster import gcs_context


from fairing import utils

logger = logging.getLogger(__name__)

class ClusterBuilder(BaseBuilder):
    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 context_source=gcs_context.GCSContextSource(),
                 image_tag=None,
                 preprocessor=None,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 dockerfile_path=None):
                super().__init__(
                        registry=registry,
                        image_name=image_name,
                        preprocessor=preprocessor,
                        base_image=base_image,
                        image_tag=image_tag
                    )
                self.manager = KubeManager()
                self.context_source = context_source

    def build(self):
        dockerfile_path = dockerfile.write_dockerfile(
            dockerfile_path=self.dockerfile_path,
            base_image=self.base_image
        )
        self.preprocessor.output_map[dockerfile_path] = 'Dockerfile'
        context_path = self.preprocessor.context_tar_gz()
        self.context_source.prepare(context_path)
        labels = {'fairing-builder': 'kaniko'}
        build_pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(
                generate_name="fairing-builder-",
                labels=labels,
            ),
            spec=self.context_source.generate_pod_spec(self.full_image_name())
        )
        created_pod = client.CoreV1Api().create_namespaced_pod("default", build_pod)
        self.manager.log(name=created_pod.metadata.name, namespace=created_pod.metadata.namespace, selectors=labels)

        # clean up created pod and secret
        self.context_source.cleanup()
        client.CoreV1Api().delete_namespaced_pod(created_pod.metadata.name, created_pod.metadata.namespace, client.V1DeleteOptions())