import pytest
import fairing
import sys
import io
import tempfile
import random

from fairing import TrainJob
from fairing.backends import KubernetesBackend, KubeflowBackend
from fairing.backends import KubeflowGKEBackend, GKEBackend, GCPManagedBackend

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
DUMMY_FN_MSG = "hello world"

# Dummy training function to be submitted
def train_fn():
    print(DUMMY_FN_MSG)

# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'

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

def test_job_submission_kubernetesbackend(capsys):
    run_submission_with_high_level_api(KubernetesBackend(), train_fn, capsys, DUMMY_FN_MSG)

def test_job_submission_kubeflowbackend(capsys):
    run_submission_with_high_level_api(KubeflowBackend(), train_fn, capsys, DUMMY_FN_MSG)