import logging
from kubernetes import client
from docker.utils.config import find_config_file
from base64 import b64encode

from kubeflow.fairing.constants import constants

logger = logging.getLogger(__name__)


def get_docker_secret():
    try:
        docker_config_file = find_config_file(config_path=None)
        with open(docker_config_file, 'r') as f:
            data = f.read()
            data = {".dockerconfigjson": b64encode(
                data.encode('utf-8')).decode("utf-8")}
        docker_secret = client.V1Secret(
            metadata=client.V1ObjectMeta(name=constants.DOCKER_CREDS_SECRET_NAME),
            data=data,
            kind="Secret",
            type="kubernetes.io/dockerconfigjson"
        )
        return docker_secret
    except Exception as e:
        logger.warning("could not get docker secret: {}".format(e))
    return None


def create_docker_secret(kube_manager, namespace):
    try:
        docker_secret = get_docker_secret()
        if docker_secret:
            kube_manager.create_secret(namespace, docker_secret)
    except Exception as e:
        logger.warning("could not create docker secret: {}".format(e))


def add_docker_credentials_if_exists(kube_manager, pod_spec, namespace):
    secret_name = constants.DOCKER_CREDS_SECRET_NAME
    try:
        if not kube_manager.secret_exists(secret_name, namespace):
            create_docker_secret(kube_manager, namespace)
        if kube_manager.secret_exists(secret_name, namespace):
            add_docker_credentials(kube_manager, pod_spec, namespace)
        else:
            logger.warning("Not able to find docker credentials secret: {}".format(secret_name))
    except Exception as e:
        logger.warning("could not check for secret: {}".format(e))


def add_docker_credentials(kube_manager, pod_spec, namespace):
    secret_name = constants.DOCKER_CREDS_SECRET_NAME
    if not kube_manager.secret_exists(secret_name, namespace):
        raise ValueError("Not able to find docker credentials secret: {}".format(secret_name))
    pod_spec.image_pull_secrets = [client.V1LocalObjectReference(secret_name)]
