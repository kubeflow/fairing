import pytest
import fairing
import sys
import io
import tempfile
import random
import time
import uuid

from google.cloud import storage
from kubernetes import client

from fairing.constants import constants

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

def get_job_with_labels(namespace,labels):
        api_instance = client.BatchV1Api()
        return api_instance.list_namespaced_job(
                namespace,
                label_selector=labels)

def run_submission_with_function_preprocessor(capsys, deployer="job", builder="append",
                                              cleanup=False, namespace="default",
                                               pvc_name=None, pvc_mount_path=None):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    fairing.config.set_builder(builder, base_image=base_image, registry=DOCKER_REGISTRY)

    expected_result = str(uuid.uuid4())
    fairing.config.set_deployer(deployer, namespace=namespace, cleanup=cleanup,
                                labels={'pytest-id': expected_result}, stream_log=False,
                                pvc_name=pvc_name, pvc_mount_path=pvc_mount_path)

    remote_train = fairing.config.fn(lambda : train_fn(expected_result))
    remote_train()
    job_detail = str(get_job_with_labels(namespace,'pytest-id=' + expected_result))
    assert expected_result in job_detail
    assert pvc_name in job_detail
    if pvc_mount_path:
        assert pvc_mount_path in job_detail
    else:
        assert constants.PVC_DEFAULT_MOUNT_PATH in job_detail

# test pvc mounting for Job
def test_pvc_mounting(capsys):
    run_submission_with_function_preprocessor(capsys, deployer="job", pvc_name='testpvc', pvc_mount_path='/pvcpath')

# Test default mount path
def test_pvc_mounting_without_path(capsys):
    run_submission_with_function_preprocessor(capsys, deployer="job", pvc_name='testpvc')