import pytest
import fairing
import sys
import io

# Dummy training function to be submitted
def train_fn():
    print('train_fn')

# Update module to work with function preprocessor
# TODO: Remove when the function preprocessor works with functions from
# other modules.
train_fn.__module__ = '__main__'

def test_kubeflow_submission():
    gcp_project = fairing.cloud.gcp.guess_project_name()
    docker_registry = 'gcr.io/{}/fairing-job'.format(gcp_project)
    fairing.config.set_builder(
        'append', base_image='gcr.io/{}/fairing-test:latest'.format(gcp_project),
        registry=docker_registry, push=True)
    fairing.config.set_deployer('job')

    remote_train = fairing.config.fn(train_fn)

    # Capture stdout
    sys.stdout = io.StringIO()
    remote_train()
    output = sys.stdout.getvalue()
    sys.stdout = sys.__stdout__

    assert 'train_fn' in output

