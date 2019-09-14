import sys
import time
import uuid
from kubeflow import fairing

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)

# Dummy training function to be submitted


def train_fn(msg):
    for _ in range(30):
        time.sleep(0.1)
        print(msg)


# Update module to work with function preprocessor
train_fn.__module__ = '__main__'


def run_submission_with_function_preprocessor(capsys, base_image, is_match, namespace="default"):
    fairing.config.set_builder(
        "append", base_image=base_image, registry=DOCKER_REGISTRY)
    fairing.config.set_deployer("job", namespace=namespace)

    test_result = str(uuid.uuid4())
    remote_train = fairing.config.fn(lambda: train_fn(test_result))
    remote_train()
    captured = capsys.readouterr()
    if is_match:
        assert test_result in captured.out
    else:
        assert "mismatches" in captured.out


def test_py_minor_version_mismatch(capsys):
    current_py_version = ".".join([str(x) for x in sys.version_info[0:2]])
    if current_py_version == "3.6.5":
        py_version = '3.5.2'
    else:
        py_version = '3.6.5'
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    run_submission_with_function_preprocessor(capsys, base_image, False)

def test_py_patch_version_match(capsys):
    current_py_version = ".".join([str(x) for x in sys.version_info[0:2]])
    if current_py_version == "3.6.5":
        py_version = '3.6.8'
    else:
        py_version = '3.6.5'
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    run_submission_with_function_preprocessor(capsys, base_image, True)

def test_py_version_match(capsys):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    run_submission_with_function_preprocessor(capsys, base_image, True)
