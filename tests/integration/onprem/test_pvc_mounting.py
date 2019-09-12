import sys
import time
import uuid
import joblib

from kubernetes import client

from kubeflow import fairing
from kubeflow.fairing.constants import constants
from kubeflow.fairing.kubernetes.utils import mounting_pvc


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


def get_job_with_labels(namespace, labels):
    api_instance = client.BatchV1Api()
    return api_instance.list_namespaced_job(
        namespace,
        label_selector=labels)


def get_deployment_with_labels(namespace, labels):
    api_instance = client.AppsV1Api()
    return api_instance.list_namespaced_deployment(
        namespace,
        label_selector=labels)


def submit_jobs_with_pvc(capsys, cleanup=False, namespace="default", # pylint:disable=unused-argument
                         pvc_name=None, pvc_mount_path=None):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    fairing.config.set_builder(
        'append', base_image=base_image, registry=DOCKER_REGISTRY)

    if pvc_mount_path:
        pod_spec_mutators = [mounting_pvc(
            pvc_name=pvc_name, pvc_mount_path=pvc_mount_path)]
    else:
        pod_spec_mutators = [mounting_pvc(pvc_name=pvc_name)]

    expected_result = str(uuid.uuid4())
    fairing.config.set_deployer('job', namespace=namespace, cleanup=cleanup,
                                labels={'pytest-id': expected_result}, stream_log=False,
                                pod_spec_mutators=pod_spec_mutators)

    remote_train = fairing.config.fn(lambda: train_fn(expected_result))
    remote_train()
    created_job = get_job_with_labels(
        namespace, 'pytest-id=' + expected_result)
    assert pvc_name == created_job.items[0].spec.template.spec.volumes[0]\
                       .persistent_volume_claim.claim_name
    if pvc_mount_path:
        assert pvc_mount_path == created_job.items[0].spec.template.spec.containers[0]\
               .volume_mounts[0].mount_path
    else:
        assert constants.PVC_DEFAULT_MOUNT_PATH == created_job.items[
            0].spec.template.spec.containers[0].volume_mounts[0].mount_path


class TestServe(object):
    def __init__(self, model_file='test_model.dat'):
        self.model = joblib.load(model_file)

    def predict(self, X, feature_names): # pylint:disable=unused-argument
        prediction = self.model.predict(data=X)
        return [[prediction.item(0), prediction.item(0)]]


def submit_serving_with_pvc(capsys, namespace='default', pvc_name=None, pvc_mount_path=None): # pylint:disable=unused-argument
    fairing.config.set_builder('docker',
                               registry=DOCKER_REGISTRY,
                               base_image="seldonio/seldon-core-s2i-python3:0.4")

    if pvc_mount_path:
        pod_spec_mutators = [mounting_pvc(
            pvc_name=pvc_name, pvc_mount_path=pvc_mount_path)]
    else:
        pod_spec_mutators = [mounting_pvc(pvc_name=pvc_name)]

    expected_result = str(uuid.uuid4())
    fairing.config.set_deployer('serving', serving_class="TestServe",
                                labels={'pytest-id': expected_result},
                                service_type='ClusterIP',
                                pod_spec_mutators=pod_spec_mutators)
    fairing.config.run()

    created_deployment = get_deployment_with_labels(
        namespace, 'pytest-id=' + expected_result)

    assert pvc_name == created_deployment.items[0].spec.template.spec.volumes[0]\
                       .persistent_volume_claim.claim_name
    if pvc_mount_path:
        assert pvc_mount_path == created_deployment.items[
            0].spec.template.spec.containers[0].volume_mounts[0].mount_path
    else:
        assert constants.PVC_DEFAULT_MOUNT_PATH == created_deployment.items[
            0].spec.template.spec.containers[0].volume_mounts[0].mount_path


def test_job_pvc_mounting(capsys):
    '''Test pvc mounting for Job'''
    submit_jobs_with_pvc(capsys, pvc_name='testpvc', pvc_mount_path='/pvcpath')


def test_job_pvc_mounting_without_path(capsys):
    '''Test default mount path'''
    submit_jobs_with_pvc(capsys, pvc_name='testpvc')


def pass_test_serving_pvc_mounting(capsys):
    '''Test pvc mount for serving'''
    submit_serving_with_pvc(capsys, pvc_name='testpvc', pvc_mount_path='/pvcpath')


def pass_test_serving_pvc_mounting_without_path(capsys):
    '''Test default mount path for serving'''
    submit_serving_with_pvc(capsys, pvc_name='testpvc')
