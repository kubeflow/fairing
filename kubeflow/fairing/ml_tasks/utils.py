import docker
from docker.errors import DockerException
from ..functions.function_shim import get_execution_obj_type, ObjectType
from ..preprocessors.function import FunctionPreProcessor
from ..preprocessors.base import BasePreProcessor
from ..preprocessors.full_notebook import FullNotebookPreProcessor

def guess_preprocessor(entry_point, input_files, output_map):
    if get_execution_obj_type(entry_point) != ObjectType.NOT_SUPPORTED:
        return FunctionPreProcessor(function_obj=entry_point,
                                    input_files=input_files,
                                    output_map=output_map)
    elif isinstance(entry_point, str) and entry_point.endswith(".py"):
        input_files.append(entry_point)
        return BasePreProcessor(executable=entry_point,
                                input_files=input_files,
                                output_map=output_map)
    elif isinstance(entry_point, str) and entry_point.endswith(".ipynb"):
        return FullNotebookPreProcessor(notebook_file=entry_point, input_files=input_files
                                        , output_map=output_map)
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
