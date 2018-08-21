from enum import Enum

from fairing.builders.docker import DockerBuilder
from fairing.builders.knative import KnativeBuilder


class Builders(Enum):
    DOCKER = 1
    KNATIVE = 2

def get_container_builder(builder_str=None):
    if builder_str == None:
        return get_default_container_builder()
    
    try:
        builder = Builders[builder_str.upper()]
    except KeyError:
        raise ValueError("Unsupported builder type: ", builder_str)

    return get_builder(builder)

def get_default_container_builder():
    # TODO: check if we are running in kubernetes or not
    # on kubernetes default should be knative
    return get_builder(Builders.DOCKER)


def get_builder(builder):
    if builder == Builders.DOCKER:
        return DockerBuilder()
    elif builder == Builders.KNATIVE:
        return KnativeBuilder()
