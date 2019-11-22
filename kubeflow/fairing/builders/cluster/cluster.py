import logging
import uuid

from kubernetes import client

from kubeflow.fairing import utils
from kubeflow.fairing.builders.base_builder import BaseBuilder
from kubeflow.fairing.builders import dockerfile
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.manager import KubeManager

logger = logging.getLogger(__name__)


class ClusterBuilder(BaseBuilder):
    """Builds a docker image in a Kubernetes cluster.
    """

    def __init__(self,
                 registry=None,
                 image_name=constants.DEFAULT_IMAGE_NAME,
                 context_source=None,
                 preprocessor=None,
                 push=True,
                 base_image=constants.DEFAULT_BASE_IMAGE,
                 pod_spec_mutators=None,
                 namespace=None,
                 dockerfile_path=None,
                 cleanup=False):
        super().__init__(
            registry=registry,
            image_name=image_name,
            push=push,
            preprocessor=preprocessor,
            base_image=base_image,
            dockerfile_path=dockerfile_path)
        self.manager = KubeManager()
        if context_source is None:
            raise RuntimeError("context_source is not specified")
        self.context_source = context_source
        self.pod_spec_mutators = pod_spec_mutators or []
        self.namespace = namespace or utils.get_default_target_namespace()
        self.cleanup = cleanup

    def build(self):
        logging.info("Building image using cluster builder.")
        install_reqs_before_copy = self.preprocessor.is_requirements_txt_file_present()
        if self.dockerfile_path:
            dockerfile_path = self.dockerfile_path
        else:
            dockerfile_path = dockerfile.write_dockerfile(
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
        pod_spec = self.context_source.generate_pod_spec(
            self.image_tag, self.push)
        for fn in self.pod_spec_mutators:
            fn(self.manager, pod_spec, self.namespace)

        pod_spec_template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(
                generate_name="fairing-builder-",
                labels=labels,
                namespace=self.namespace,
                annotations={"sidecar.istio.io/inject": "false"},
            ),
            spec=pod_spec
        )
        job_spec = client.V1JobSpec(
            template=pod_spec_template,
            parallelism=1,
            completions=1,
            backoff_limit=0,
        )
        build_job = client.V1Job(
            api_version="batch/v1",
            kind="Job",
            metadata=client.V1ObjectMeta(
                generate_name="fairing-builder-",
                labels=labels,
            ),
            spec=job_spec
        )
        created_job = client. \
            BatchV1Api(). \
            create_namespaced_job(self.namespace, build_job)

        self.manager.log(
            name=created_job.metadata.name,
            namespace=created_job.metadata.namespace,
            selectors=labels,
            container="kaniko")

        # Invoke upstream clean ups
        self.context_source.cleanup()
        # Cleanup build_job if requested by user
        # Otherwise build_job will be cleaned up by Kubernetes GC
        if self.cleanup:
            logging.warning("Cleaning up job {}...".format(created_job.metadata.name))
            client. \
                BatchV1Api(). \
                delete_namespaced_job(
                    created_job.metadata.name,
                    created_job.metadata.namespace,
                    body=client.V1DeleteOptions(propagation_policy='Foreground')
                )
