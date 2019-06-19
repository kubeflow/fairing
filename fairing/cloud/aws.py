import boto3
from botocore.exceptions import ClientError
from fairing.constants import constants
from kubernetes import client
import logging

import os
import json

logger = logging.getLogger(__name__)


class S3Uploader(object):
    def __init__(self, region):
        self.region = region
        self.storage_client = boto3.client('s3', region_name=region)

    def upload_to_bucket(self,
                         blob_name,
                         bucket_name,
                         file_to_upload):
        self.create_bucket_if_not_exists(bucket_name)
        self.storage_client.upload_file(file_to_upload, bucket_name, blob_name)
        return "s3://{}/{}".format(bucket_name, blob_name)

    def create_bucket_if_not_exists(self, bucket_name):
        try:
            self.storage_client.head_bucket(Bucket=bucket_name)
        except ClientError:
            self.storage_client.create_bucket(Bucket=bucket_name,
                                              CreateBucketConfiguration={'LocationConstraint': self.region})


def guess_account_id():
    account_id = boto3.client('sts').get_caller_identity()["Account"]

    if account_id is None:
        raise Exception('Could not determine account id.')

    return account_id


def add_aws_credentials_if_exists(kube_manager, pod_spec, namespace):
    try:
        if kube_manager.secret_exists(constants.AWS_CREDS_SECRET_NAME, namespace):
            add_aws_credentials(kube_manager, pod_spec, namespace)
        else:
            logger.warning("Not able to find aws credentials secret: {}".format(constants.AWS_CREDS_SECRET_NAME))
    except Exception as e:
        logger.warn("could not check for secret: {}".format(e))


def add_aws_credentials(kube_manager, pod_spec, namespace):
    if not kube_manager.secret_exists(constants.AWS_CREDS_SECRET_NAME, namespace):
        raise ValueError('Unable to mount credentials: '
        + 'Secret aws-credentials not found in namespace {}'.format(namespace))

    # Set appropriate secrets and volumes to enable kubeflow-user service
    # account.
    volume_mount = client.V1VolumeMount(
        name='aws-credentials', mount_path='/root/.aws/', read_only=True)
    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    volume = client.V1Volume(
        name='aws-credentials',
        secret=client.V1SecretVolumeSource(secret_name=constants.AWS_CREDS_SECRET_NAME))
    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]
