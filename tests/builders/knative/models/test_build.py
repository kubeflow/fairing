from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest

from fairing.builders.knative.models.build import Build

@pytest.fixture
def build():
    return Build(metadata=None, spec=None)

@pytest.mark.parametrize("status, expected", [
    ({'status': {'conditions': [{'state': 'Succeeded', 'status': 'True'}]}}, True),
    ({'status': {'conditions': [{'state': 'Succeeded', 'status': 'False'}]}}, False),
    ({'status': {'conditions': [{'state': 'Succeeded', 'status': 'Unknown'}]}}, None),
    ({'status': {'conditions': [{'state': 'OtherState', 'status': 'dummy'}]}}, None),
    ({'status': 'malformed-obhect'}, None)
])
def test_check_build_succeeded(build, status, expected):
    assert build.check_build_succeeded(status) == expected