import pytest
import sys
import random
import os
from kubeflow import fairing
from google.cloud import storage


GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
GCS_SUCCESS_MSG = "gcs access is successful"
GCS_FAILED_MSG = 'does not have storage.buckets.get access'


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
train_fn_with_gcs_access.__module__ = '__main__'


def run_submission_with_gcs_access(deployer, pod_spec_mutators, namespace,
                                   gcs_prefix, capsys, expected_result):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    fairing.config.set_builder(
        'docker', base_image=base_image,
        registry=DOCKER_REGISTRY, push=True)
    fairing.config.set_deployer(
        deployer, pod_spec_mutators=pod_spec_mutators, namespace=namespace)
    requirements_file = os.path.relpath(os.path.join(
        os.path.dirname(__file__), 'requirements.txt'))
    fairing.config.set_preprocessor('function',
                                    function_obj=lambda: train_fn_with_gcs_access(
                                        gcs_prefix),
                                    output_map={requirements_file: '/app/requirements.txt'})
    fairing.config.run()
    captured = capsys.readouterr()
    assert expected_result in captured.out


#def test_job_submission_with_gcs_access(capsys, temp_gcs_prefix):
#    run_submission_with_gcs_access(
#        'job',
#        pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials_if_exists],
#        namespace='kubeflow-fairing',
#        gcs_prefix=temp_gcs_prefix,
#        capsys=capsys,
#        expected_result=GCS_SUCCESS_MSG)


def test_tfjob_submission_with_gcs_access(capsys, temp_gcs_prefix):
    run_submission_with_gcs_access(
        'tfjob',
        pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials_if_exists],
        namespace='kubeflow-fairing',
        gcs_prefix=temp_gcs_prefix,
        capsys=capsys,
        expected_result=GCS_SUCCESS_MSG)


def test_job_submission_without_gcs_access(capsys, temp_gcs_prefix):
    run_submission_with_gcs_access(
        'job',
        pod_spec_mutators=[],
        namespace='kubeflow-fairing',
        gcs_prefix=temp_gcs_prefix,
        capsys=capsys,
        expected_result=GCS_FAILED_MSG)

def test_tfjob_submission_without_gcs_access(capsys, temp_gcs_prefix):
    run_submission_with_gcs_access(
        'tfjob',
        pod_spec_mutators=[],
        namespace='kubeflow-fairing',
        gcs_prefix=temp_gcs_prefix,
        capsys=capsys,
        expected_result=GCS_FAILED_MSG)


def test_job_submission_invalid_namespace(capsys, temp_gcs_prefix):
    with pytest.raises(ValueError) as err:
        run_submission_with_gcs_access(
            'job',
            pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
            namespace='default',
            gcs_prefix=temp_gcs_prefix,
            capsys=capsys,
            expected_result=None)

    msg = 'Unable to mount credentials: '\
          'Secret user-gcp-sa not found in namespace default'
    assert msg in str(err.value)


def test_tfjob_submission_invalid_namespace(capsys, temp_gcs_prefix):
    with pytest.raises(ValueError) as err:
        run_submission_with_gcs_access(
            'tfjob',
            pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
            namespace='default',
            gcs_prefix=temp_gcs_prefix,
            capsys=capsys,
            expected_result=None)

    msg = 'Unable to mount credentials: '\
          'Secret user-gcp-sa not found in namespace default'
    assert msg in str(err.value)
