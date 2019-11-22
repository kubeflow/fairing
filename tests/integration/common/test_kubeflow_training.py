import sys
import time
import uuid
import os

from kubernetes import client

from kubeflow import fairing
from kubeflow.fairing.builders.cluster import gcs_context
from kubeflow.fairing.constants import constants

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)

# Dummy training function to be submitted


def train_fn(msg):
    for _ in range(30):
        time.sleep(0.1)
        print(msg)


# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'


def get_tfjobs_with_labels(labels):
    api_instance = client.CustomObjectsApi()
    return api_instance.list_cluster_custom_object(
        constants.TF_JOB_GROUP,
        constants.TF_JOB_VERSION,
        constants.TF_JOB_PLURAL,
        label_selector=labels)


def run_submission_with_function_preprocessor(capsys, deployer="job", builder="append",
                                              namespace="default", dockerfile_path=None,
                                              cleanup=False):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    if builder == 'cluster':
        if dockerfile_path is None:
            fairing.config.set_builder(builder, base_image=base_image, registry=DOCKER_REGISTRY,
                                       pod_spec_mutators=[
                                           fairing.cloud.gcp.add_gcp_credentials_if_exists],
                                       context_source=gcs_context.GCSContextSource(
                                           namespace=namespace),
                                       namespace=namespace)
        else:
            fairing.config.set_builder(builder, registry=DOCKER_REGISTRY,
                                       dockerfile_path=dockerfile_path,
                                       pod_spec_mutators=[
                                           fairing.cloud.gcp.add_gcp_credentials_if_exists],
                                       context_source=gcs_context.GCSContextSource(
                                           namespace=namespace),
                                       namespace=namespace)
    else:
        fairing.config.set_builder(
            builder, base_image=base_image, registry=DOCKER_REGISTRY)

    expected_result = str(uuid.uuid4())
    fairing.config.set_deployer(deployer, namespace=namespace, cleanup=cleanup,
                                labels={'pytest-id': expected_result})

    remote_train = fairing.config.fn(lambda: train_fn(expected_result))
    remote_train()
    captured = capsys.readouterr()
    assert expected_result in captured.out

    if deployer == "tfjob":
        if cleanup:
            assert expected_result not in str(
                get_tfjobs_with_labels('pytest-id=' + expected_result))
        else:
            assert expected_result in str(
                get_tfjobs_with_labels('pytest-id=' + expected_result))


def test_job_deployer(capsys):
    run_submission_with_function_preprocessor(capsys, deployer="job")


def test_tfjob_deployer(capsys):
    run_submission_with_function_preprocessor(
        capsys, deployer="tfjob", namespace="kubeflow-fairing")


def test_tfjob_deployer_cleanup(capsys):
    run_submission_with_function_preprocessor(capsys, deployer="tfjob",
                                              namespace="kubeflow-fairing", cleanup=True)


def test_docker_builder(capsys):
    run_submission_with_function_preprocessor(capsys, builder="docker")


def test_cluster_builder(capsys):
    run_submission_with_function_preprocessor(
        capsys, builder="cluster", namespace="kubeflow-fairing")


def test_cluster_builder_with_dockerfile(capsys):
    dir_path = os.path.dirname(os.path.realpath(__file__))
    run_submission_with_function_preprocessor(
        capsys, builder="cluster", dockerfile_path=dir_path + "/Dockerfile.test",
        namespace="kubeflow-fairing")
