import docker
import fairing

from docker.errors import DockerException
from fairing.builders.docker.docker import DockerBuilder
from fairing.builders.cluster.cluster import ClusterBuilder
from fairing.builders.append.append import AppendBuilder
from fairing.functions.function_shim import get_execution_obj_type, ObjectType
from fairing.preprocessors.function import FunctionPreProcessor


def guess_preprocessor(entry_point, *args, **kwargs):
    if get_execution_obj_type(entry_point) != ObjectType.NOT_SUPPORTED:
        return FunctionPreProcessor(entry_point, *args, **kwargs)
    else:
        # TODO (karthikv2k) Handle other entrypoints like python files and full notebooks
        raise NotImplementedError(
            "obj param should be a function or a class, got {}".format(type(entry_point)))


def is_docker_daemon_exists():
    try:
        docker.APIClient(version='auto')
        return True
    except DockerException:
        return False


def guess_builder(needs_deps_installation):
    if fairing.utils.is_running_in_k8s():
        return ClusterBuilder
    elif is_docker_daemon_exists():
        return DockerBuilder
    elif not needs_deps_installation:
        return AppendBuilder
    else:
        # TODO (karthikv2k): Add more info on how to reolve this issue
        raise RuntimeError("Not able to guess the right builder for this job!")
