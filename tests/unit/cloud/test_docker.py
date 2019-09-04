
from fairing.cloud.docker import get_docker_secret_spec
from fairing.constants import constants


def test_docker_secret_spec():
   docker_secret=get_docker_secret_spec()
   print(docker_secret)
   assert docker_secret.metadata.name == constants.DOCKER_CREDS_SECRET_NAME