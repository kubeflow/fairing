import json
import base64
import ibm_boto3
from ibm_botocore.exceptions import ClientError
from kubernetes import client

from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.manager import KubeManager
from kubeflow.fairing import utils

class COSUploader(object):
    """
    IBM Cloud Object Storage Uploader.

    :param namespace(str): namespace that IBM COS credential secret created in.
    :param cos_endpoint_url(str): IBM COS endpoint url, such as "https://s3..."
    """
    def __init__(self, namespace=None,
                 cos_endpoint_url=constants.IBM_COS_DEFAULT_ENDPOINT):
        self.namespace = namespace or utils.get_default_target_namespace()

        aws_access_key_id, aws_secret_accesss_key = get_ibm_cos_credentials(self.namespace)

        self.client = ibm_boto3.client(
            "s3",
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_accesss_key,
            endpoint_url=cos_endpoint_url
        )

    def create_bucket(self, bucket_name):
        """
        Create Bucket in IBM Cloud Object Storage.

        :param bucket_name(str): Bucket name.
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
        except ClientError:
            self.client.create_bucket(Bucket=bucket_name)

    def upload_to_bucket(self, blob_name, bucket_name, file_to_upload):
        """
        Uploaded file to IBM Cloud Object Storage.

        :param bucket_name(str): The path to the file to upload.
        :param bucket_name(str): The name of the bucket to upload to.
        :param bucket_name(str): The name of the key to upload to.
        """
        self.create_bucket(bucket_name)
        self.client.upload_file(file_to_upload, bucket_name, blob_name)
        return "s3://{}/{}".format(bucket_name, blob_name)


def get_ibm_cos_credentials(namespace):
    """
    Get the IBM COS credential from secret.

    :param namespace(str): The namespace that IBM COS credential secret created in.
    """
    secret_name = constants.IBM_COS_CREDS_SECRET_NAME
    if not KubeManager().secret_exists(secret_name, namespace):
        raise Exception("Secret '{}' not found in namespace '{}'".format(secret_name, namespace))

    secret = client.CoreV1Api().read_namespaced_secret(secret_name, namespace)
    creds_data = secret.data[constants.IBM_COS_CREDS_FILE_NAME]
    creds_json = base64.b64decode(creds_data).decode('utf-8')

    cos_creds = json.loads(creds_json)
    if cos_creds.get('cos_hmac_keys', ''):
        aws_access_key_id = cos_creds['cos_hmac_keys'].get('access_key_id', '')
        aws_secret_accesss_key = cos_creds['cos_hmac_keys'].get('secret_access_key', '')
    else:
        raise RuntimeError("Kaniko needs AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY\
                           if using S3 Bucket. Please use HMAC Credential.")

    return aws_access_key_id, aws_secret_accesss_key
