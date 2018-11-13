from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
import pytest

from fairing.builders import get_container_builder,  KnativeBuilder, DockerBuilder

def test_default_get_container_builder():
    assert type(get_container_builder()) == DockerBuilder

def test_get_container_builder():
    assert type(get_container_builder('docker')) == DockerBuilder
    assert type(get_container_builder('knative')) == KnativeBuilder

    with pytest.raises(ValueError):
        get_container_builder('wrong_key')
