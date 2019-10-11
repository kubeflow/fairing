import sys
import time
import uuid
from kubeflow import fairing

from kubeflow.fairing import TrainJob
from kubeflow.fairing.backends.backends import KubernetesBackend, KubeflowBackend

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
TEST_GCS_BUCKET = '{}-fairing'.format(GCS_PROJECT_ID)
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


def run_submission_with_high_level_api(backend, capsys):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'python:{}'.format(py_version)

    expected_result = str(uuid.uuid4())
    train_job = TrainJob(entry_point=lambda: train_fn(expected_result),
                         base_docker_image=base_image,
                         docker_registry=DOCKER_REGISTRY,
                         backend=backend,
                         input_files=["requirements.txt"])
    train_job.submit()
    captured = capsys.readouterr()
    assert expected_result in captured.out


def test_job_submission_kubernetesbackend(capsys):
    run_submission_with_high_level_api(KubernetesBackend(), capsys)


def test_job_submission_kubeflowbackend(capsys):
    run_submission_with_high_level_api(KubeflowBackend(), capsys)
