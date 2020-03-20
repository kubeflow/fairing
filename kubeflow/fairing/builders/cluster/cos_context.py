from kubernetes import client
from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface
from kubeflow.fairing.cloud import ibm_cloud
from kubeflow.fairing import utils
from kubeflow.fairing.constants import constants

class COSContextSource(ContextSourceInterface):
    """
    IBM Cloud Object Storage Context Source.

    :param namespace: namespace that IBM COS credential secret created in.
    :param region: region name, default to us-geo
    :param cos_endpoint_url: IBM COS endpoint url, such as "https://s3..."
    """
    def __init__(self, namespace=None, region='us-geo',
                 cos_endpoint_url=constants.IBM_COS_DEFAULT_ENDPOINT):
        self.cos_endpoint_url = cos_endpoint_url
        self.region = region
        self.namespace = namespace or utils.get_default_target_namespace()
        self.aws_access_key_id, self.aws_secret_access_key =\
            ibm_cloud.get_ibm_cos_credentials(namespace)

    def prepare(self, context_filename):  # pylint: disable=arguments-differ
        """
        :param context_filename: context filename
        """
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        """
        :param context_filename: context filename
        """
        cos_uploader = ibm_cloud.COSUploader(
            self.namespace,
            self.cos_endpoint_url
        )

        context_hash = utils.crc(context_filename)
        bucket_name = 'kubeflow-' + context_hash.lower()
        return cos_uploader.upload_to_bucket(blob_name='fairing-builds/' +
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
                    image=constants.KANIKO_IMAGE,
                    args=args,
                    env=[
                        client.V1EnvVar(name='AWS_REGION',
                                        value=self.region),
                        client.V1EnvVar(name='AWS_ACCESS_KEY_ID',
                                        value=self.aws_access_key_id),
                        client.V1EnvVar(name='AWS_SECRET_ACCESS_KEY',
                                        value=self.aws_secret_access_key),
                        client.V1EnvVar(name='S3_ENDPOINT',
                                        value=self.cos_endpoint_url),
                    ],
                    volume_mounts=[
                        client.V1VolumeMount(name="docker-config",
                                             mount_path="/kaniko/.docker/")
                    ]
                )
            ],
            restart_policy='Never',
            volumes=[
                client.V1Volume(name="docker-config",
                                config_map=client.V1ConfigMapVolumeSource(
                                    name="docker-config"))
            ])

    def cleanup(self):
        # TODO(@jinchihe)
        pass
