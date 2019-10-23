import docker
from docker.errors import DockerException
from kubeflow.fairing.functions.function_shim import get_execution_obj_type, ObjectType
from kubeflow.fairing.preprocessors.function import FunctionPreProcessor
from kubeflow.fairing.preprocessors.base import BasePreProcessor
from kubeflow.fairing.preprocessors.full_notebook import FullNotebookPreProcessor

def guess_preprocessor(entry_point, input_files, output_map):
    """Preprocessor to use to modify inputs before sending them to docker build

    :param entry_point: entry_point which to use
    :param input_files: input files
    :param output_map: output

    """
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
    """To check if docker daemon exists or not. """
    try:
        docker.APIClient(version='auto')
        return True
    except DockerException:
        return False
