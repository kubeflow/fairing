from kubeflow.fairing.kubernetes import utils as k8s_utils
from kubernetes.client.models.v1_pod_spec import V1PodSpec
from kubernetes.client.models.v1_container import V1Container


def test_resource_mutator():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    k8s_utils.get_resource_mutator(cpu=1.5, memory=0.5)(None, pod_spec, "")
    actual = pod_spec.containers[0].resources.limits
    expected = {'cpu': 1.5, 'memory': '0.47Gi'}
    assert actual == expected


def test_resource_mutator_no_cpu():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    k8s_utils.get_resource_mutator(memory=0.5)(None, pod_spec, "")
    actual = pod_spec.containers[0].resources.limits
    expected = {'memory': '0.47Gi'}
    assert actual == expected


def test_resource_mutator_no_mem():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    k8s_utils.get_resource_mutator(cpu=1.5)(None, pod_spec, "")
    actual = pod_spec.containers[0].resources.limits
    expected = {'cpu': 1.5}
    assert actual == expected

def test_resource_mutator_gpu():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    k8s_utils.get_resource_mutator(gpu=1)(None, pod_spec, "")
    actual = pod_spec.containers[0].resources.limits
    expected = {'nvidia.com/gpu': 1}
    assert actual == expected

def test_resource_mutator_gpu_vendor():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    k8s_utils.get_resource_mutator(gpu=2, gpu_vendor='amd')(None, pod_spec, "")
    actual = pod_spec.containers[0].resources.limits
    expected = {'amd.com/gpu': 2}
    assert actual == expected
