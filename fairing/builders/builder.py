from enum import Enum

from fairing.builders.knative import KnativeBuilder
from fairing.builders.cmbuilder import CmBuilder
from fairing.utils import is_running_in_k8s

class Builders(Enum):
    DOCKER = 1
    KNATIVE = 2
    CM = 3

def get_container_builder(builder_str=None):
    if builder_str == None:
        return get_default_container_builder()
    
    try:
        builder = Builders[builder_str.upper()]
    except KeyError:
        raise ValueError("Unsupported builder type: ", builder_str)

    return get_builder(builder)

def get_default_container_builder():
    if is_running_in_k8s():
        return get_builder(Builders.KNATIVE)
    return get_builder(Builders.DOCKER)


def get_builder(builder):
    if builder == Builders.DOCKER:
        from fairing.builders.docker import DockerBuilder
        return DockerBuilder()
    elif builder == Builders.KNATIVE:
        return KnativeBuilder()
    elif builder == Builders.CM:
        return CmBuilder()
