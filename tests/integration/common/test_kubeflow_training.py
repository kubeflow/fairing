import pytest
import fairing
import sys
import io
import tempfile
import random

from google.cloud import storage
from fairing import TrainJob
from fairing.backends import KubernetesBackend, KubeflowBackend
from fairing.backends import KubeflowGKEBackend, GKEBackend, GCPManagedBackend

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
DUMMY_FN_MSG = "hello world"

# Dummy training function to be submitted
def train_fn():
    print(DUMMY_FN_MSG)

# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'

def run_submission_with_function_preprocessor(capsys, expected_result, deployer="job", builder="append", namespace="default"):
    base_image = 'gcr.io/{}/fairing-test:latest'.format(GCS_PROJECT_ID)
    fairing.config.set_builder('append', base_image=base_image, registry=DOCKER_REGISTRY)
    fairing.config.set_deployer(deployer, namespace=namespace)

    remote_train = fairing.config.fn(train_fn)
    remote_train()
    captured = capsys.readouterr()
    assert expected_result in captured.out

def test_job_deployer(capsys):
    run_submission_with_function_preprocessor(capsys, DUMMY_FN_MSG, deployer="job")    

def test_tfjob_deployer(capsys):
    run_submission_with_function_preprocessor(capsys, DUMMY_FN_MSG, deployer="tfjob", namespace="kubeflow") 

def test_docker_builder(capsys):
    run_submission_with_function_preprocessor(capsys, DUMMY_FN_MSG, builder="docker")    

def test_cluster_builder(capsys):
    run_submission_with_function_preprocessor(capsys, DUMMY_FN_MSG, builder="cluster", namespace="kubeflow")
