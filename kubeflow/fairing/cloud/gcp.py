import google.auth
from google.cloud import storage
from google.cloud.exceptions import NotFound
from kubeflow.fairing.constants import constants
from kubernetes import client
import logging

import os
import json

logger = logging.getLogger(__name__)


class GCSUploader(object):
    def __init__(
            self,
            credentials_file=os.environ.get(constants.GOOGLE_CREDS_ENV)): #pylint:disable=unused-argument
        self.storage_client = storage.Client()

    def upload_to_bucket(self,
                         blob_name,
                         bucket_name,
                         file_to_upload):
        bucket = self.get_or_create_bucket(bucket_name)
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(file_to_upload)
        return "gs://{}/{}".format(bucket_name, blob_name)

    def get_or_create_bucket(self, bucket_name):
        try:
            bucket = self.storage_client.get_bucket(bucket_name)
            return bucket
        except NotFound:
            bucket = self.storage_client.create_bucket(bucket_name)
            return bucket


def guess_project_name(credentials_file=None):
    # Check credentials file if provided
    if credentials_file is not None:
        with open(credentials_file, 'r') as f:
            data = f.read()
        parsed_creds_file = json.loads(data)
        return parsed_creds_file['project_id']

    # Use the google.auth library to retrieve credentials. Checks the following
    # locations in order:
    # 1. GOOGLE_APPLICATION_CREDENTIALS environment variable
    # 2. Google Cloud SDK (gcloud)
    # 3. App Engine Identity service
    # 4. Compute Engine Metadata service
    credentials, project_id = google.auth.default() #pylint:disable=unused-variable

    if project_id is None:
        raise Exception('Could not determine project id.')

    return project_id


def add_gcp_credentials_if_exists(kube_manager, pod_spec, namespace):
    try:
        if kube_manager.secret_exists(constants.GCP_CREDS_SECRET_NAME, namespace):
            add_gcp_credentials(kube_manager, pod_spec, namespace)
        else:
            logger.warning("Not able to find gcp credentials secret: {}"\
                           .format(constants.GCP_CREDS_SECRET_NAME))
            logger.warning("Trying workload identity service account: {}"\
                           .format(constants.GCP_SERVICE_ACCOUNT_NAME))
            pod_spec.service_account_name = constants.GCP_SERVICE_ACCOUNT_NAME
    except Exception as e:
        logger.warning("could not check for secret: {}".format(e))


def add_gcp_credentials(kube_manager, pod_spec, namespace):
    """Note: This method will be deprecated soon and will become unavailable by 1.0.
             All future access will use Workload Identity.
    """
    if not kube_manager.secret_exists(constants.GCP_CREDS_SECRET_NAME, namespace):
        raise ValueError('Unable to mount credentials: '
                         + 'Secret user-gcp-sa not found in namespace {}'.format(namespace))

    # Set appropriate secrets and volumes to enable kubeflow-user service
    # account.
    env_var = client.V1EnvVar(
        name='GOOGLE_APPLICATION_CREDENTIALS',
        value='/etc/secrets/user-gcp-sa.json')
    if pod_spec.containers[0].env:
        pod_spec.containers[0].env.append(env_var)
    else:
        pod_spec.containers[0].env = [env_var]

    volume_mount = client.V1VolumeMount(
        name='user-gcp-sa', mount_path='/etc/secrets', read_only=True)
    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    volume = client.V1Volume(
        name='user-gcp-sa',
        secret=client.V1SecretVolumeSource(secret_name='user-gcp-sa'))
    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]

def get_default_docker_registry():
    try:
        return 'gcr.io/{}/fairing-job'.format(guess_project_name())
    except Exception:
        return None
