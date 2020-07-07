from kubernetes import client
from kubernetes.client.models.v1_pod_spec import V1PodSpec
from kubernetes.client.models.v1_container import V1Container

from kubeflow.fairing.kubernetes import utils as k8s_utils


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

def test_add_env_no_env():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image"
    )],)
    env_vars = {'var1': 'value1', 'var2': 'value2'}
    k8s_utils.add_env(env_vars=env_vars)(None, pod_spec, "")
    actual = pod_spec.containers[0].env
    expected = [
        {'name': 'var1', 'value': 'value1', 'value_from': None},
        {'name': 'var2', 'value': 'value2', 'value_from': None}
    ]
    assert str(actual) == str(expected)

def test_add_env_has_env():
    pod_spec = V1PodSpec(containers=[V1Container(
        name='model',
        image="image",
        env=[client.V1EnvVar(name='var0', value='value0')]
    )],)
    env_vars = {'var1': 'value1', 'var2': 'value2'}
    k8s_utils.add_env(env_vars=env_vars)(None, pod_spec, "")
    actual = pod_spec.containers[0].env
    expected = [
        {'name': 'var0', 'value': 'value0', 'value_from': None},
        {'name': 'var1', 'value': 'value1', 'value_from': None},
        {'name': 'var2', 'value': 'value2', 'value_from': None}
    ]
    assert str(actual) == str(expected)
