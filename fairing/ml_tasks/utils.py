import docker
import fairing

from docker.errors import DockerException
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
