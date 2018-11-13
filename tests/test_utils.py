from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest

from fairing.utils import is_runtime_phase, get_image_full, get_image

REPO_NAME = 'testrepo'
IMAGE_NAME = 'fairing-test'
IMAGE_TAG = 'some-tag'

@pytest.mark.parametrize("runtime_phase", [True, False])
def test_is_runtime_phase(runtime_phase, monkeypatch):
    if runtime_phase:
        monkeypatch.setenv("FAIRING_RUNTIME", True)
    assert is_runtime_phase() == runtime_phase

def test_get_image_full():
    img = get_image_full(REPO_NAME, IMAGE_NAME, IMAGE_TAG)
    assert img == '{}/{}:{}'.format(REPO_NAME, IMAGE_NAME, IMAGE_TAG)

def test_get_image():
    img = get_image(REPO_NAME, IMAGE_NAME)
    assert img == '{}/{}'.format(REPO_NAME, IMAGE_NAME)
