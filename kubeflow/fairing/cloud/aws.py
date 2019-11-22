import boto3
import logging
import re
from botocore.exceptions import ClientError
from kubernetes import client

from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)

class S3Uploader(object):
    """ For AWS S3 up load """
    def __init__(self, region):
        self.region = region
        self.storage_client = boto3.client('s3', region_name=region)

    def upload_to_bucket(self,
                         blob_name,
                         bucket_name,
                         file_to_upload):
        """Upload a file to an S3 bucket

        :param blob_name: S3 object name
        :param bucket_name: Bucket to upload to
        :param file_to_upload: File to upload

        """
        self.create_bucket_if_not_exists(bucket_name)
        self.storage_client.upload_file(file_to_upload, bucket_name, blob_name)
        return "s3://{}/{}".format(bucket_name, blob_name)

    def create_bucket_if_not_exists(self, bucket_name):
        """Create bucket if this bucket not exists

        :param bucket_name: Bucket name

        """
        try:
            self.storage_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            bucket = {'Bucket': bucket_name}
            if self.region != 'us-east-1':
                bucket['CreateBucketConfiguration'] = {'LocationConstraint': self.region}
            self.storage_client.create_bucket(**bucket)


def guess_account_id():
    """ Get account id """
    account_id = boto3.client('sts').get_caller_identity()["Account"]

    if account_id is None:
        raise Exception('Could not determine account id.')

    return account_id


def add_aws_credentials_if_exists(kube_manager, pod_spec, namespace):
    """add AWS credential

    :param kube_manager: kube manager for handles communication with Kubernetes' client
    :param pod_spec: pod spec like volumes and security context
    :param namespace: The custom resource

    """
    try:
        if kube_manager.secret_exists(constants.AWS_CREDS_SECRET_NAME, namespace):
            add_aws_credentials(kube_manager, pod_spec, namespace)
        else:
            logger.warning("Not able to find aws credentials secret: {}"
                           .format(constants.AWS_CREDS_SECRET_NAME))
    except Exception as e:
        logger.warning("could not check for secret: {}".format(e))


def add_aws_credentials(kube_manager, pod_spec, namespace):
    """add AWS credential

    :param kube_manager: kube manager for handles communication with Kubernetes' client
    :param pod_spec: pod spec like volumes and security context
    :param namespace: The custom resource

    """
    if not kube_manager.secret_exists(constants.AWS_CREDS_SECRET_NAME, namespace):
        raise ValueError('Unable to mount credentials: Secret aws-secret not found in namespace {}'
                         .format(namespace))

    # Set appropriate secrets env to enable kubeflow-user service
    # account.
    env = [
        client.V1EnvVar(
            name='AWS_ACCESS_KEY_ID',
            value_from=client.V1EnvVarSource(
                secret_key_ref=client.V1SecretKeySelector(
                    name=constants.AWS_CREDS_SECRET_NAME,
                    key='AWS_ACCESS_KEY_ID'
                )
            )
        ),
        client.V1EnvVar(
            name='AWS_SECRET_ACCESS_KEY',
            value_from=client.V1EnvVarSource(
                secret_key_ref=client.V1SecretKeySelector(
                    name=constants.AWS_CREDS_SECRET_NAME,
                    key='AWS_SECRET_ACCESS_KEY'
                )
            )
        )]

    if pod_spec.containers[0].env:
        pod_spec.containers[0].env.extend(env)
    else:
        pod_spec.containers[0].env = env


def add_ecr_config(kube_manager, pod_spec, namespace):
    """add secret

    :param kube_manager: kube manager for handles communication with Kubernetes' client
    :param pod_spec: pod spec like volumes and security context
    :param namespace: The custom resource

    """
    if not kube_manager.secret_exists('ecr-config', namespace):
        secret = client.V1Secret(metadata=client.V1ObjectMeta(name='ecr-config'),
                                 string_data={
                                     'config.json': '{"credsStore": "ecr-login"}'
                                 })
        kube_manager.create_secret(namespace, secret)

    volume_mount = client.V1VolumeMount(name='ecr-config',
                                        mount_path='/kaniko/.docker/', read_only=True)

    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    volume = client.V1Volume(name='ecr-config',
                             secret=client.V1SecretVolumeSource(secret_name='ecr-config'))

    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]


def is_ecr_registry(registry):
    """verify secrte registy

    :param registry: registry

    """
    pattern = r'(.+)\.dkr\.ecr\.(.+)\.amazonaws\.com'
    return bool(re.match(pattern, registry))


def create_ecr_registry(registry, repository):
    """create secret registry

    :param registry: registry
    :param repository: repository name

    """
    registry = registry.split('.')
    registry_id = registry[0]
    region = registry[3]

    ecr_client = boto3.client('ecr', region_name=region)

    try:
        ecr_client.describe_repositories(registryId=registry_id,
                                         repositoryNames=[repository])
    except ClientError:
        ecr_client.create_repository(repositoryName=repository)
