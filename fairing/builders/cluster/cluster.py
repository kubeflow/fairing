import logging
import uuid

from kubernetes import client

from fairing.builders.base_builder import BaseBuilder
from fairing.builders import dockerfile
from fairing.constants import constants
from fairing.kubernetes.manager import KubeManager
from fairing.builders.cluster import gcs_context

logger = logging.getLogger(__name__)


class ClusterBuilder(BaseBuilder):
    """Builds a docker image in a Kubernetes cluster.


     Args:
        registry (str): Required. Registry to push image to
                        Example: gcr.io/kubeflow-images
        base_image (str): Base image to use for the image build
        preprocessor (BasePreProcessor): Preprocessor to use to modify inputs
                                         before sending them to docker build
        context_source (ContextSourceInterface): context available to the
                                                 cluster build
        push {bool} -- Whether or not to push the image to the registry
    """
    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 context_source=None,
                 preprocessor=None,
                 push=True,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 pod_spec_mutators=None,
                 namespace="kubeflow",
                 dockerfile_path=None):
        super().__init__(
                registry=registry,
                image_name=image_name,
                push=push,
                preprocessor=preprocessor,
                base_image=base_image,
            )
        self.manager = KubeManager()
        if context_source is None:
            context_source = gcs_context.GCSContextSource(namespace=namespace)
        self.context_source = context_source
        self.pod_spec_mutators = pod_spec_mutators or []
        self.namespace = namespace

    def build(self):
        logging.info("Building image using cluster builder.")
        install_reqs_before_copy = self.preprocessor.is_requirements_txt_file_present()
        dockerfile_path = dockerfile.write_dockerfile(
            dockerfile_path=self.dockerfile_path,
            path_prefix=self.preprocessor.path_prefix,
            base_image=self.base_image,
            install_reqs_before_copy=install_reqs_before_copy
        )
        self.preprocessor.output_map[dockerfile_path] = 'Dockerfile'
        context_path, context_hash = self.preprocessor.context_tar_gz()
        self.image_tag = self.full_image_name(context_hash)
        self.context_source.prepare(context_path)
        labels = {'fairing-builder': 'kaniko'}
        labels['fairing-build-id'] = str(uuid.uuid1())
        pod_spec = self.context_source.generate_pod_spec(self.image_tag, self.push)
        for fn in self.pod_spec_mutators:
            fn(self.manager, pod_spec, self.namespace)
        build_pod = client.V1Pod(
            api_version="v1",
            kind="Pod",
            metadata=client.V1ObjectMeta(
                generate_name="fairing-builder-",
                labels=labels,
                namespace=self.namespace,
            ),
            spec=pod_spec
        )
        created_pod = client. \
            CoreV1Api(). \
            create_namespaced_pod(self.namespace, build_pod)
        self.manager.log(
            name=created_pod.metadata.name,
            namespace=created_pod.metadata.namespace,
            selectors=labels)

        # clean up created pod and secret
        self.context_source.cleanup()
        client.CoreV1Api().delete_namespaced_pod(
            created_pod.metadata.name,
            created_pod.metadata.namespace,
            body=client.V1DeleteOptions())
