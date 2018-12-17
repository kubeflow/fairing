from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import os
import pytest
import json
from fairing.backend.kubernetes import KubeManager
from mock import MagicMock, patch, Mock

def test_append_dict_to_specs():
    # setup
    append_dict = {
        'env': [{'name':'y', 'value': 'yval'}, {'name': 'z', 'value': 'zval'}],
        'volumeMounts': [{'name': 'hostTemp', 'mountPath': '/host/tmp'}],
        'volumes': [{'name': 'hostTemp', 'hostPath': {'path': '/tmp', 'type': 'Directory'}}]
    }
    spec_list = []
    worker_pod_spec = {'spec': {'containers': [
        {'name': 'tensorflow','env': [{'name': 'x', 'value':'xval'}]},
        {'name': 'init', 'env': [{'a': 'aval'}]},
    ]}}
    chief_pod_spec = {'spec': {'containers': [
        {'name': 'tensorflow', 'volumeMounts': [{'name': 'vol1', 'mountPath': '/vol'}]},
        {'name': 'init', 'env': [{'name': 'a', 'value': 'aval'}]},
    ]}, 'volumes': [{'name': 'vol1', 'emptyDir': {}}]}
    spec_list.append(worker_pod_spec)
    spec_list.append(chief_pod_spec)
    # run
    KubeManager.append_dict_to_specs(spec_list, append_dict)
    # Verify
    compare_spec_with_append_list(append_dict, spec_list)


def compare_spec_with_append_list(append_dict, spec_list):
    for spec in spec_list:
        tensorflow_container = [c for c in filter(lambda x: x['name'] == 'tensorflow',
                                                  spec['spec']['containers'])][0]
        for key, value in append_dict.items():
            if key == 'volumes':
                continue
            print("value {}, container {}".format(value, tensorflow_container[key]))
            for d in value:
                dj = json.dumps(d, sort_keys=True)
                found = False
                for d1 in tensorflow_container[key]:
                    d1j = json.dumps(d1, sort_keys=True)
                    if dj == d1j:
                        found = True
                        break
                if not found:
                    raise AssertionError('dict {} not found in container {}'.format(d, tensorflow_container[key]))


@patch('kubernetes.config.load_kube_config', MagicMock(return_value=None))
def test_configmap_tf_job_template():
    ## setup
    # get mock pod spec
    # container env, volume_mounts, and volumes should be arrays of dicts
    pod_template_spec = MagicMock()
    container = MagicMock()
    e1 = MagicMock()
    e1.to_dict.return_value = {'name':'y', 'value': 'yval'}
    e2 = MagicMock()
    e2.to_dict.return_value = {'name': 'z', 'value': 'zval'}
    container.env.__iter__.return_value = [e1, e2]
    vm = MagicMock()
    vm.to_dict.return_value = {'name': 'hostTemp', 'mountPath': '/host/tmp'}
    container.volumeMounts.__iter__.return_value = [vm]
    v = MagicMock()
    v.to_dict.return_value = {'name': 'hostTemp', 'hostPath': {'path': '/tmp', 'type': 'Directory'}}
    pod_template_spec.spec.volumes.__iter__.return_value = [v]
    pod_template_spec.spec.containers.__getitem__.return_value = container

    # mock KubeManager.load_configmap
    # mock tf_job dict with worker, chief, and PS specs
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tfjob-template.yaml')) as f:
        tf_job = f.read()
    cm = {'tfjob-template.yaml': tf_job}
    name = 'test-configmap'
    namespace = 'test-namespace'
    worker_count = 10
    ps_count = 1
    kubemanager = KubeManager()
    with patch('fairing.backend.kubernetes.KubeManager.load_configmap', MagicMock(return_value=cm)):
        ## run
        tf_job_output = kubemanager.configmap_tf_job_template(name=name,
                                              namespace=namespace,
                                              pod_template_spec=pod_template_spec,
                                              worker_count=worker_count,
                                              ps_count=ps_count)

    ## validate
    spec_list = KubeManager.populate_spec_list(tf_job_output)
    append_dict = {
        "env": [
            {
                "name": "y",
                "value": "yval"
            },
            {
                "name": "z",
                "value": "zval"
            }
        ],
        "volumeMounts": [
            {
                "name": "hostTemp",
                "mountPath": "/host/tmp"
            }
        ],
        "volumes": [
            {
                "name": "hostTemp",
                "hostPath": {
                    "path": "/tmp",
                    "type": "Directory"
                }
            }
        ]
    }
    for t in ['Worker', 'Chief', 'Ps', 'Evaluator']:
        assert t in tf_job_output['spec']['tfReplicaSpecs']
    compare_spec_with_append_list(append_dict, spec_list)


def test_log():
    pass
