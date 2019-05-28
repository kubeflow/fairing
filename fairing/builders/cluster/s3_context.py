import os

from fairing.cloud import aws
from fairing import utils
from fairing.constants import constants
from fairing.kubernetes.manager import client, KubeManager
from fairing.builders.cluster.context_source import ContextSourceInterface


class S3ContextSource(ContextSourceInterface):
    def __init__(self,
                 aws_account=None,
                 credentials_file=None,
                 namespace='default',
                 region=None):
        self.aws_account = aws_account
        self.manager = KubeManager()
        self.namespace = namespace
        self.region = region

    def prepare(self, context_filename):
        if self.aws_account is None:
            self.aws_account = aws.guess_account_id()
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        s3_uploader = aws.S3Uploader(self.region)
        context_hash = utils.crc(context_filename)
        return s3_uploader.upload_to_bucket(
                    bucket_name='kubeflow-' + self.aws_account + '-' + self.region,
                    blob_name='fairing_builds/' + context_hash,
                    file_to_upload=context_filename)

    def cleanup(self):
        pass

    def generate_pod_spec(self, image_name, push):
        args = ["--dockerfile=Dockerfile",
                          "--destination=" + image_name,
                          "--context=" + self.uploaded_context_url]
        if not push:
            args.append("--no-push")

        if not self.manager.secret_exists('ecr-config', self.namespace):
            secret = client.V1Secret(
                metadata = client.V1ObjectMeta(name='ecr-config'),
                string_data={
                    'config.json': '{"credsStore": "ecr-login"}'
                })
            self.manager.create_secret(self.namespace, secret)

        return client.V1PodSpec(
                containers=[client.V1Container(
                    name='kaniko',
                    image='gcr.io/kaniko-project/executor:v0.7.0',
                    args=["--dockerfile=Dockerfile",
                          "--destination=" + image_name,
                          "--context=" + self.uploaded_context_url],
                    env=[client.V1EnvVar(
                        name='AWS_REGION',
                        value=self.region)],
                    volume_mounts=[client.V1VolumeMount(
                        name='ecr-config', mount_path='/kaniko/.docker/', read_only=True)]
                )],
                volumes=[client.V1Volume(
                    name='ecr-config',
                    secret=client.V1SecretVolumeSource(secret_name='ecr-config'))],
                restart_policy='Never'
            )
