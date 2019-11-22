import os

from kubeflow.fairing.cloud import gcp
from kubeflow.fairing import utils
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.manager import client, KubeManager
from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface

class GCSContextSource(ContextSourceInterface):
    """Google cloud storage context for docker builder"""
    def __init__(self,
                 gcp_project=None,
                 credentials_file=os.environ.get(constants.GOOGLE_CREDS_ENV),
                 namespace='default'):
        self.gcp_project = gcp_project
        self.credentials_file = credentials_file
        self.manager = KubeManager()
        self.namespace = namespace

    def prepare(self, context_filename):  # pylint:disable=arguments-differ
        if self.gcp_project is None:
            self.gcp_project = gcp.guess_project_name()
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        gcs_uploader = gcp.GCSUploader()
        context_hash = utils.crc(context_filename)
        return gcs_uploader.upload_to_bucket(bucket_name=self.gcp_project,
                                             blob_name='fairing_builds/' + context_hash,
                                             file_to_upload=context_filename)

    def cleanup(self):
        pass

    def generate_pod_spec(self, image_name, push):  # pylint:disable=arguments-differ
        args = ["--dockerfile=Dockerfile",
                "--destination=" + image_name,
                "--context=" + self.uploaded_context_url,
                "--cache=true"]
        if not push:
            args.append("--no-push")

        return client.V1PodSpec(
            containers=[client.V1Container(
                name='kaniko',
                image=constants.KANIKO_IMAGE,
                args=args,
            )],
            restart_policy='Never'
        )
