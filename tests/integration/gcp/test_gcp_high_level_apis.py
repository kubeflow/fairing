import sys
import random
import time
import uuid

from google.cloud import storage
from kubeflow import fairing
from kubeflow.fairing import TrainJob
#from kubeflow.fairing.backends import KubeflowGKEBackend, GKEBackend, GCPManagedBackend
from kubeflow.fairing.backends import KubeflowGKEBackend, GCPManagedBackend

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
GCS_SUCCESS_MSG = "gcs access is successful"
GCS_FAILED_MSG = 'google.api_core.exceptions.Forbidden: 403'


def delete_blobs1(bucket_name, prefix):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    for blob in bucket.list_blobs(prefix=prefix):
        print("deleting {}".format(blob.name))
        blob.delete()

# Dummy training function to be submitted


def train_fn(msg):
    for _ in range(30):
        time.sleep(0.1)
        print(msg)

# Training function that accesses GCS


def train_fn_with_gcs_access(temp_gcs_prefix):
    rnd_number = random.randint(0, 10**9)
    gcs_filename = '{}/gcs_test_file_{}.txt'.format(
        temp_gcs_prefix, rnd_number)

    client = storage.Client()
    bucket_name = '{}-fairing'.format(client.project)
    bucket = client.get_bucket(bucket_name)

    # Upload file to GCS
    rnd_str = str(random.randint(0, 10**9))
    bucket.blob(gcs_filename).upload_from_string(rnd_str)

    # Download and read the file
    file_contents = bucket.blob(
        gcs_filename).download_as_string().decode("utf-8")
    if file_contents == rnd_str:
        print(GCS_SUCCESS_MSG)
    else:
        print("gcs content mismatch, expected:'{}' got: '{}'".format(
            rnd_str, file_contents))


# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'
train_fn_with_gcs_access.__module__ = '__main__'


def run_submission_with_high_level_api(backend, entry_point, capsys, expected_result):

    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'python:{}'.format(py_version)

    train_job = TrainJob(entry_point=entry_point,
                         base_docker_image=base_image,
                         docker_registry=DOCKER_REGISTRY,
                         backend=backend,
                         input_files=["requirements.txt"])
    train_job.submit()
    captured = capsys.readouterr()
    assert expected_result in captured.out


def test_job_submission_kubeflowgkebackend(capsys):
    expected_result = str(uuid.uuid4())
    run_submission_with_high_level_api(
        KubeflowGKEBackend(namespace='kubeflow-fairing'),
        lambda: train_fn(expected_result), capsys, expected_result)


def test_job_submission_kubeflowgkebackend_gcs_access(capsys, temp_gcs_prefix):
    run_submission_with_high_level_api(
        KubeflowGKEBackend(namespace='kubeflow-fairing'),
        lambda: train_fn_with_gcs_access(temp_gcs_prefix), capsys, GCS_SUCCESS_MSG)


# Disabling the following tests that launch jobs in 'default' namespace.
# 'default' namespace is no longer available to fairing
#def test_job_submission_gkebackend_with_default_namespace(capsys):
#    expected_result = str(uuid.uuid4())
#    run_submission_with_high_level_api(GKEBackend(), lambda: train_fn(
#        expected_result), capsys, expected_result)
#
#
#def test_job_submission_gkebackend_gcs_access_with_default_namespace(capsys, temp_gcs_prefix):
#    run_submission_with_high_level_api(GKEBackend(), lambda: train_fn_with_gcs_access(
#        temp_gcs_prefix), capsys, GCS_FAILED_MSG)
#

#def test_job_submission_gkebackend_gcs_access_with_kubeflow_namespace(capsys, temp_gcs_prefix):
#    run_submission_with_high_level_api(GKEBackend(namespace="kubeflow-fairing"),
#                                       lambda: train_fn_with_gcs_access(temp_gcs_prefix),
#                                       capsys, GCS_SUCCESS_MSG)

def test_job_submission_gcpmanaged(capsys, temp_gcs_prefix):
    # TODO (karthikv2k): test the job output, blocked by #146
    run_submission_with_high_level_api(GCPManagedBackend(), lambda: train_fn_with_gcs_access(
        temp_gcs_prefix), capsys, 'Job submitted successfully.')
