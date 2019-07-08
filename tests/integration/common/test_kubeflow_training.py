import pytest
import fairing
import sys
import io
import tempfile
import random
import time
import uuid

from google.cloud import storage
from fairing import TrainJob
from fairing.backends import KubernetesBackend, KubeflowBackend
from fairing.backends import KubeflowGKEBackend, GKEBackend, GCPManagedBackend
from fairing.builders.cluster import gcs_context

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

def run_submission_with_function_preprocessor(capsys, caplog, deployer="job", builder="append", namespace="default", cleanup=False):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    if builder=='cluster':
        fairing.config.set_builder(builder, base_image=base_image, registry=DOCKER_REGISTRY,
                                   pod_spec_mutators=[fairing.cloud.gcp.add_gcp_credentials],
                                   context_source=gcs_context.GCSContextSource(namespace=namespace))
    else:
        fairing.config.set_builder(builder, base_image=base_image, registry=DOCKER_REGISTRY)
    fairing.config.set_deployer(deployer, namespace=namespace, cleanup=cleanup)

    expected_result = str(uuid.uuid4())
    remote_train = fairing.config.fn(lambda : train_fn(expected_result))
    remote_train()
    captured = capsys.readouterr()
    assert expected_result in captured.out
    if cleanup:
        assert "Cleaning up" in caplog.text
    else:
        assert "Cleaning up" not in caplog.text

def test_job_deployer(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, deployer="job")

def test_job_deployer_cleanup(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, deployer="job", cleanup=True)

def test_tfjob_deployer(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, deployer="tfjob", namespace="kubeflow")

def test_tfjob_deployer_cleanup(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, deployer="tfjob", namespace="kubeflow", cleanup=True)

def test_docker_builder(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, builder="docker")

def test_cluster_builder(capsys, caplog):
    run_submission_with_function_preprocessor(capsys, caplog, builder="cluster", namespace="kubeflow")
