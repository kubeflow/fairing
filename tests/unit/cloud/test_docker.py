from kubeflow.fairing.cloud.docker import get_docker_secret
from kubeflow.fairing.constants import constants
import json
import os


def test_docker_secret_spec():
    os.environ["DOCKER_CONFIG"] = "/tmp"
    config_dir = os.environ.get('DOCKER_CONFIG')
    config_file_name = 'config.json'
    config_file = os.path.join(config_dir, config_file_name)
    with open(config_file, 'w+') as f:
        json.dump({'config': "config"}, f)
    docker_secret = get_docker_secret()
    assert docker_secret.metadata.name == constants.DOCKER_CREDS_SECRET_NAME
    os.remove(config_file)
