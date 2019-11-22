from kubeflow.fairing.cloud import aws
from kubeflow.fairing import utils
from kubeflow.fairing.kubernetes.manager import client, KubeManager
from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface
from kubeflow.fairing.constants import constants


class S3ContextSource(ContextSourceInterface):
    """aws S3 context for docker builder"""
    def __init__(self,
                 aws_account=None,
                 region=None,
                 bucket_name=None):
        self.aws_account = aws_account
        self.manager = KubeManager()
        self.region = region or 'us-east-1'
        self.bucket_name = bucket_name

    def prepare(self, context_filename):  # pylint:disable=arguments-differ
        """

        :param context_filename: context filename

        """
        if self.aws_account is None:
            self.aws_account = aws.guess_account_id()
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        """

        :param context_filename: context filename

        """
        s3_uploader = aws.S3Uploader(self.region)
        context_hash = utils.crc(context_filename)
        bucket_name = self.bucket_name or 'kubeflow-' + \
            self.aws_account + '-' + self.region
        return s3_uploader.upload_to_bucket(bucket_name=bucket_name,
                                            blob_name='fairing_builds/' + context_hash,
                                            file_to_upload=context_filename)

    def cleanup(self):
        pass

    def generate_pod_spec(self, image_name, push):  # pylint:disable=arguments-differ
        args = ["--dockerfile=Dockerfile",
                "--destination=" + image_name,
                "--context=" + self.uploaded_context_url]
        if not push:
            args.append("--no-push")

        return client.V1PodSpec(
            containers=[client.V1Container(name='kaniko',
                                           image=constants.KANIKO_IMAGE,
                                           args=["--dockerfile=Dockerfile",
                                                 "--destination=" + image_name,
                                                 "--context=" + self.uploaded_context_url],
                                           env=[client.V1EnvVar(name='AWS_REGION',
                                                                value=self.region)])],
            restart_policy='Never')
