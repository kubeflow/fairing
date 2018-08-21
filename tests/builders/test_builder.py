import pytest

from fairing.builders import get_container_builder, DockerBuilder, KnativeBuilder

def test_default_get_container_builder():
    assert type(get_container_builder()) == DockerBuilder

def test_get_container_builder():
    assert type(get_container_builder('docker')) == DockerBuilder
    assert type(get_container_builder('knative')) == KnativeBuilder

    with pytest.raises(ValueError):
        get_container_builder('wrong_key')
