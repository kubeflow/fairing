import pytest

from fairing.utils import is_runtime_phase, get_image
from fairing.options import PackageOptions

REPO_NAME = 'testrepo'
IMAGE_NAME = 'fairing-test'


@pytest.fixture
def package_options():
  return {'name': IMAGE_NAME, 'repository': REPO_NAME, 'publish': True}

@pytest.mark.parametrize("runtime_phase", [True, False])
def test_is_runtime_phase(runtime_phase, monkeypatch):
    if runtime_phase:
        monkeypatch.setenv("FAIRING_RUNTIME", True)
    assert is_runtime_phase() == runtime_phase

def test_get_image(package_options):
  img = get_image(PackageOptions(**package_options))
  tag = 'latest'
  assert img == '{}/{}:{}'.format(REPO_NAME, IMAGE_NAME, tag)