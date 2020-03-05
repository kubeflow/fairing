from os.path import isfile
from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.builders.podman.podman import PodmanBuilder

MOCK_CMD_BUILD = 'podman build -t <image_tag> - < <context_file>'
MOCK_CMD_PUSH = 'podman push <image_tag> --tls-verify=<tls_verify>'

def test_podman_builder():
    """
    test podman builder
    """
    podmanBuilder = PodmanBuilder(
        registry="test-image-registry",
        preprocessor=BasePreProcessor(),
        tls_verify=True)
    cmd_build = podmanBuilder.gen_cmd('build')
    cmd_push = podmanBuilder.gen_cmd('publish')

    # Test docker context exists
    assert isfile(podmanBuilder.context_file)

    # Test if the podman build cmd is correct
    mock_cmd_build = MOCK_CMD_BUILD \
        .replace('<image_tag>', podmanBuilder.image_tag) \
        .replace('<context_file>', podmanBuilder.context_file)
    assert cmd_build == mock_cmd_build

    # Test if the podman push cmd is correct
    mock_cmd_push = MOCK_CMD_PUSH \
        .replace('<image_tag>', podmanBuilder.image_tag) \
        .replace('<tls_verify>', str(podmanBuilder.tls_verify).lower())
    assert cmd_push == mock_cmd_push
