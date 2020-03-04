from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface
from kubeflow.fairing.cloud import k8s
from kubeflow.fairing.kubernetes.manager import client, KubeManager
from kubeflow.fairing import utils
from kubeflow.fairing import constants

constants.constants.KANIKO_IMAGE = "gcr.io/kaniko-project/executor:v0.14.0"


class MinioContextSource(ContextSourceInterface):
    def __init__(self, endpoint_url, minio_secret, minio_secret_key,
                 region_name):
        self.endpoint_url = endpoint_url
        self.minio_secret = minio_secret
        self.minio_secret_key = minio_secret_key
        self.region_name = region_name
        self.Manager = KubeManager()

    def prepare(self, context_filename):  # pylint: disable=arguments-differ
        """
        :param context_filename: context filename
        """
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        minio_uploader = k8s.MinioUploader(self.endpoint_url,
                                           self.minio_secret,
                                           self.minio_secret_key,
                                           self.region_name)
        context_hash = utils.crc(context_filename)
        bucket_name = 'kubeflow-' + self.region_name
        return minio_uploader.upload_to_bucket(blob_name='fairing-builds/' +
                                               context_hash,
                                               bucket_name=bucket_name,
                                               file_to_upload=context_filename)

    def generate_pod_spec(self, image_name, push):  # pylint: disable=arguments-differ
        """
        :param image_name: name of image to be built
        :param push: whether to push image to given registry or not
        """
        args = [
            "--dockerfile=Dockerfile",
            "--destination=" + image_name,
            "--context=" + self.uploaded_context_url
        ]
        if not push:
            args.append("--no-push")

        return client.V1PodSpec(
            containers=[
                client.V1Container(
                    name='kaniko',
                    image=constants.constants.KANIKO_IMAGE,
                    args=args,
                    env=[
                        client.V1EnvVar(name='AWS_REGION',
                                        value=self.region_name),
                        client.V1EnvVar(name='AWS_ACCESS_KEY_ID',
                                        value=self.minio_secret),
                        client.V1EnvVar(name='AWS_SECRET_ACCESS_KEY',
                                        value=self.minio_secret_key),
                        client.V1EnvVar(name='S3_ENDPOINT',
                                        value=self.endpoint_url),
                        client.V1EnvVar(name='S3_FORCE_PATH_STYLE',
                                        value="true")
                    ],
                    volume_mounts=[
                        client.V1VolumeMount(name="docker-config",
                                             mount_path="/kaniko/.docker/")
                    ],
                )
            ],
            restart_policy='Never',
            volumes=[
                client.V1Volume(name="docker-config",
                                config_map=client.V1ConfigMapVolumeSource(
                                    name="docker-config"))
            ])

    def cleanup(self):
        # TODO(swiftdiaries)
        pass
