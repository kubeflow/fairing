import pytest

from fairing.architectures.native.basic import BasicArchitecture

@pytest.fixture
def architecture():
    return BasicArchitecture()

@pytest.mark.parametrize("job_count", [1, 10, 100])
def test_add_training(architecture, job_count):
    svc = {}
    img_name = 'test/test:1.0'
    name = 'test'
    exp = {'jobs': [{
            'name': name,
            'parallelism': job_count,
            'completion': job_count,
            'containers': [{'image': img_name, 'volumeMounts': []}],
            'volumes': []
            }]}
    assert exp == architecture.add_jobs(svc, job_count, img_name, name, [], [])