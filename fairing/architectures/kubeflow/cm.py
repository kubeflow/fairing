from fairing.architectures.kubeflow.basic import BasicArchitecture
from fairing.backend.kubeflow import KubeflowBackend
from fairing.notebook_helper import get_notebook_name
from fairing.kubeclient import KubeClient
from jinja2 import Template
import subprocess
import os
import logging
import yaml
import json
logger = logging.getLogger(__name__)

class CMTraining(BasicArchitecture):
    def __init__(self, ps_count, worker_count, notebook):
        self.ps_count = ps_count
        self.worker_count = worker_count
        self.notebook = notebook
        self.client = KubeClient()

    def add_jobs(self, svc, count, repository, img, name, volumes, volume_mounts):
        worker_image = os.environ['WORKER_IMAGE_NAME'] or img
        ps_image = os.environ["PS_IMAGE_NAME"]
        nb_name = self.notebook or get_notebook_name()
        nb_full_path = os.path.join(os.getcwd(), nb_name)
        cmd = "jupyter nbconvert --to python {} --output /tmp/code".format(nb_full_path).split()
        subprocess.check_call(cmd)

        with open('/tmp/code.py', 'rb') as f:
            code = f.read()
        configMap = {
            "apiVersion": "v1",
            "kind": "ConfigMap",
            "metadata": {
               "name": name
            },
            "data": {
                "code.py": code
            }
        }
        svc["configMap"] = configMap
        volume_mounts = volume_mounts or []
        volume_mounts.append({
            "name": "code",
            "mountPath": "/code"
        })
        volumes = volumes or []
        volumes.append({
            "name": 'code',
            "configMap": {
                "name": name
            }
        })
        cmd = "python /code/code.py".split()
        # TODO: This should come from configs
        # append configmap to volume and volumeMounts
        config_map = self.client.load_configmap(name='tfjob-template')
        template = Template(config_map['tfjob-template.yaml'])
        str = template.render(name=name, worker_image=worker_image, ps_image=ps_image, cmd=cmd,
                              worker_count=self.worker_count, ps_count=self.ps_count)

        svc["tfJob"] = yaml.load(str)
        logger.debug("Configmap %s", json.dumps(svc["configMap"], indent=1))
        logger.info("tfjob yaml\n %s", str)
        logger.debug("tfjob dict %s", json.dumps(svc["tfJob"], indent=1))
        return svc

    def get_associated_backend(self):
        return KubeflowBackend()
