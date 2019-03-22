import pytest
import fairing
import sys
import io
import tempfile

from google.cloud import storage

# Dummy training function to be submitted
def train_fn():
    print('hello world')

# Training function that accesses GCS
def train_fn_with_gcs_access():
    gcs_filename = 'gcs_test_file.txt'

    client = storage.Client()
    bucket_name = '{}-fairing'.format(client.project)
    bucket = client.get_bucket(bucket_name)

    # Delete file if exists
    if bucket.get_blob(gcs_filename):
        bucket.delete_blob(gcs_filename)

    # Upload file to GCS
    bucket.blob(gcs_filename).upload_from_string('testing gcs access')

    # Download and read the file
    file_contents = bucket.blob(gcs_filename).download_as_string()
    print(file_contents)

# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'
train_fn_with_gcs_access.__module__ = '__main__'

def test_job_submission(capsys):
    gcp_project = fairing.cloud.gcp.guess_project_name()
    docker_registry = 'gcr.io/{}/fairing-job'.format(gcp_project)
    fairing.config.set_builder(
        'append', base_image='gcr.io/{}/fairing-test:latest'.format(gcp_project),
        registry=docker_registry, push=True)
    fairing.config.set_deployer('job')

    remote_train = fairing.config.fn(train_fn)
    remote_train()

    captured = capsys.readouterr()
    assert 'hello world' in captured.out


def run_submission_with_gcs_access(deployer, pod_spec_mutators, namespace):
    gcp_project = fairing.cloud.gcp.guess_project_name()
    docker_registry = 'gcr.io/{}/fairing-job'.format(gcp_project)
    fairing.config.set_builder(
        'append', base_image='gcr.io/{}/fairing-test:latest'.format(gcp_project),
        registry=docker_registry, push=True)
    fairing.config.set_deployer(
        deployer, pod_spec_mutators=pod_spec_mutators, namespace=namespace)

    remote_train = fairing.config.fn(train_fn_with_gcs_access)
    remote_train()

def test_job_submission_with_gcs_access(capsys):
    run_submission_with_gcs_access(
        'job',
        pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
        namespace='kubeflow')

    captured = capsys.readouterr()
    assert 'testing gcs access' in captured.out

def test_tfjob_submission_with_gcs_access(capsys):
    run_submission_with_gcs_access(
        'tfjob',
        pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
        namespace='kubeflow')

    captured = capsys.readouterr()
    assert 'testing gcs access' in captured.out

def test_job_submission_without_gcs_access(capsys):
    run_submission_with_gcs_access(
        'job',
        pod_spec_mutators=[],
        namespace='kubeflow')

    captured = capsys.readouterr()
    assert 'google.api_core.exceptions.Forbidden: 403' in captured.out

def test_tfjob_submission_without_gcs_access(capsys):
    run_submission_with_gcs_access(
        'tfjob',
        pod_spec_mutators=[],
        namespace='kubeflow')

    captured = capsys.readouterr()
    assert 'google.api_core.exceptions.Forbidden: 403' in captured.out

def test_job_submission_invalid_namespace(capsys):
    with pytest.raises(ValueError) as err:
        run_submission_with_gcs_access(
            'job',
            pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
            namespace='default')

    msg = 'Unable to mount credentials: '\
          'Secret user-gcp-sa not found in namespace default'
    assert msg in str(err.value)

def test_tfjob_submission_invalid_namespace(capsys):
    with pytest.raises(ValueError) as err:
        run_submission_with_gcs_access(
            'tfjob',
            pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
            namespace='default')

    msg = 'Unable to mount credentials: '\
          'Secret user-gcp-sa not found in namespace default'
    assert msg in str(err.value)

