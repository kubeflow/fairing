from fairing.cloud.docker import add_docker_credentials_if_exists
from fairing.constants import constants
from fairing.kubernetes.manager import KubeManager
from kubernetes import client
import json
import os


def test_docker_secret_spec():
    os.environ["DOCKER_CONFIG"] = "/tmp"
    config_dir = os.environ.get('DOCKER_CONFIG')
    config_file_name = 'config.json'
    config_file = os.path.join(config_dir, config_file_name)
    with open(config_file, 'w+') as f:
        json.dump({'config': "config"}, f)
    pod_spec = client.V1PodSpec(
       containers=[client.V1Container(name="test")]
    )
    add_docker_credentials_if_exists(KubeManager(), pod_spec, "default")
    assert pod_spec.image_pull_secrets[0].name == \
           constants.DOCKER_CREDS_SECRET_NAME
