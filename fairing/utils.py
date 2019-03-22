import os
import zlib
import uuid
import docker

from docker.errors import DockerException

def get_image(repository, name):
    return "{repo}/{name}".format(
        repo=repository,
        name=name
    )


def is_running_in_k8s():
    return os.path.isdir('/var/run/secrets/kubernetes.io/')


def get_current_k8s_namespace():
    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
        return f.readline()


def get_default_target_namespace():
    if not is_running_in_k8s():
        return 'default'
    return get_current_k8s_namespace()


def crc(file_name):
    prev = 0
    for eachLine in open(file_name, "rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X" % (prev & 0xFFFFFFFF)

def random_tag():
    return str(uuid.uuid4()).split('-')[0]


def guess_preprocessor(entry_point, *args, **kwargs):
    #Trying to avoid any clyclic dependencies by importing locally within the method
    from fairing.functions.function_shim import get_execution_obj_type, ObjectType
    from fairing.preprocessors.function import FunctionPreProcessor
    
    if get_execution_obj_type(entry_point) != ObjectType.NOT_SUPPORTED:
        return FunctionPreProcessor(entry_point, *args, **kwargs)
    else:
        raise NotImplementedError(
            "obj param should be a function or a class, got {}".format(type(entry_point)))


def guess_docker_registry():
    import fairing
    try:
        gcp_project = fairing.cloud.gcp.guess_project_name()
        registry = 'gcr.io/{}'.format(gcp_project)
        return registry
    except Exception as e:
        print(e)
        return None


def is_docker_daemon_exists():
    try:
        docker.APIClient(version='auto')
        return True
    except DockerException:
        return False


def guess_builder(needs_deps_installation):
    #Trying to avoid any clyclic dependencies by importing locally within the method
    from fairing.builders.docker.docker import DockerBuilder
    from fairing.builders.cluster.cluster import ClusterBuilder
    from fairing.builders.append.append import AppendBuilder

    if is_running_in_k8s():
        return ClusterBuilder
    elif is_docker_daemon_exists():
        return DockerBuilder
    elif not needs_deps_installation:
        return AppendBuilder
    else:
        #TODO (karthikv2k): Add more info on how to reolve this issue
        raise RuntimeError("Not able to guess the right builder for this job!")
