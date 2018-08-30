import pytest

from fairing.utils import is_runtime_phase, get_image_full, get_image
from fairing.options import PackageOptions

REPO_NAME = 'testrepo'
IMAGE_NAME = 'fairing-test'
IMAGE_TAG = 'some-tag'

@pytest.fixture
def package_options():
    return {'name': IMAGE_NAME, 'tag': IMAGE_TAG, 'repository': REPO_NAME, 'publish': True}


@pytest.mark.parametrize("runtime_phase", [True, False])
def test_is_runtime_phase(runtime_phase, monkeypatch):
    if runtime_phase:
        monkeypatch.setenv("FAIRING_RUNTIME", True)
    assert is_runtime_phase() == runtime_phase


def test_get_image_full(package_options):
    img = get_image_full(PackageOptions(**package_options))
    tag = 'test'
    assert img == '{}/{}:{}'.format(REPO_NAME, IMAGE_NAME, IMAGE_TAG)


def test_get_image(package_options):
    img = get_image(PackageOptions(**package_options))
    assert img == '{}/{}'.format(REPO_NAME, IMAGE_NAME)
