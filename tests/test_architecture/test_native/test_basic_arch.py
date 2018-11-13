from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest

from fairing.architectures.native.basic import BasicArchitecture
from fairing.utils import get_image_full
@pytest.fixture
def architecture():
    return BasicArchitecture()

@pytest.mark.parametrize("job_count", [1, 10, 100])
def test_add_training(architecture, job_count):
    svc = {}

    repo = 'test'
    image_name = 'testimage'
    image_tag = '1.0'
    full_image_name = get_image_full(repo, image_name, image_tag)
    exp = {'jobs': [{
            'name': image_name,
            'parallelism': job_count,
            'completion': job_count,
            'containers': [{'image': full_image_name, 'volumeMounts': []}],
            'volumes': []
            }]}
    assert exp == architecture.add_jobs(svc, job_count, repo, image_name, image_tag, [], [])