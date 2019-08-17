import logging
from fairing.constants import constants
from kubernetes import client
from docker.utils.config import find_config_file
logger = logging.getLogger(__name__)


def create_docker_secret(kube_manager,namespace):
    from base64 import b64encode
    docker_config_file = find_config_file(config_path=None)
    f = open(docker_config_file, "r")
    data = f.read()
    data = {".dockerconfigjson": b64encode(
        data.encode('utf-8')).decode("utf-8")}
    f.close()
    docker_secret = client.V1Secret(
            metadata=client.V1ObjectMeta(
                name=constants.DOCKER_CREDS_SECRET_NAME
            ),
            data=data,
            kind="Secret",
            type="kubernetes.io/dockerconfigjson"
        )
    kube_manager.create_docker_secret(namespace, docker_secret)


def add_docker_credentials_if_exists(kube_manager, pod_spec, namespace):
    try:
        if not kube_manager.secret_exists(constants.DOCKER_CREDS_SECRET_NAME, namespace):
            create_docker_secret(kube_manager, namespace)
        if kube_manager.secret_exists(constants.DOCKER_CREDS_SECRET_NAME, namespace):
            add_docker_credentials(kube_manager, pod_spec, namespace)
        else:
            logger.warning("Not able to find docker credentials secret: {}" \
                           .format(constants.DOCKER_CREDS_SECRET_NAME))
    except Exception as e:
        logger.warning("could not check for secret: {}".format(e))


def add_docker_credentials(kube_manager, pod_spec, namespace):
    if not kube_manager.secret_exists(constants.DOCKER_CREDS_SECRET_NAME, namespace):
        raise ValueError("Not able to find docker credentials secret: {}" \
                           .format(constants.DOCKER_CREDS_SECRET_NAME))
    pod_spec.image_pull_secrets = [client.V1LocalObjectReference(constants.DOCKER_CREDS_SECRET_NAME)]