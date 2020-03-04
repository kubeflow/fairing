from kubeflow.fairing.builders.cluster.context_source import ContextSourceInterface
from kubeflow.fairing.cloud import ibm_cloud
from kubeflow.fairing.kubernetes.manager import client, KubeManager
from kubeflow.fairing import utils
from kubeflow.fairing import constants
import ibm_boto3
from ibm_botocore.client import Config, ClientError

class COSContextSource(ContextSourceInterface):
    def __init__(self, cos_endpoint_url, cos_auth_endpoint, cos_api_key,
                 cos_resource_crn, cos_bucket_location=None):
        self.cos_endpoint_url = cos_endpoint_url
        self.cos_auth_endpoint = cos_auth_endpoint
        self.cos_api_key = cos_api_key
        self.cos_resource_crn = cos_resource_crn
        self.cos_bucket_location = cos_bucket_location
        self.Manager = KubeManager()

        cos_client = ibm_boto3.client("s3", 
            ibm_api_key_id=self.cos_api_key,
            ibm_service_instance_id=self.cos_resource_crn,
            ibm_auth_endpoint=self.cos_auth_endpoint,
            config=Config(signature_version="oauth"),
            endpoint_url=self.cos_endpoint_url
        )


    def prepare(self, context_filename):  # pylint: disable=arguments-differ
        """
        :param context_filename: context filename
        """
        self.uploaded_context_url = self.upload_context(context_filename)

    def upload_context(self, context_filename):
        cos_uploader = ibm_cloud.COSUploader(
            self.cos_endpoint_url,
            self.cos_auth_endpoint,
            self.cos_api_key,
            self.cos_resource_crn,
            self.cos_bucket_location,
        )

        context_hash = utils.crc(context_filename)
        bucket_name = 'kubeflow-' + context_hash
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
                    image=constants.constants.KANIKO_IMAGE,
                    args=args,
                )
            ],
            restart_policy='Never')

    def cleanup(self):
        # TODO(@jinchihe)
        pass
