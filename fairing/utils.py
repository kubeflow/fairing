import os
import zlib
import uuid


def get_image(repository, name):
    """Get the full image name by integrating repository and image name.

    :param repository: The name of repository
    :param name: The short image name
    :returns: str: Full image name, format: repo/name.

    """
    return "{repo}/{name}".format(
        repo=repository,
        name=name
    )

def is_running_in_k8s():
    """Check if running in the kubernetes cluster."""
    return os.path.isdir('/var/run/secrets/kubernetes.io/')

def get_current_k8s_namespace():
    """Get the current namespace of kubernetes."""
    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
        return f.readline()

def get_default_target_namespace():
    """Get the default target namespace, if running in the kubernetes cluster,
    will be current namespace, Otherwiase, will be "default".
    """
    if not is_running_in_k8s():
        return 'default'
    return get_current_k8s_namespace()

def crc(file_name):
    """Compute a running Cyclic Redundancy Check checksum.

    :param file_name: The file name that's for crc checksum.

    """
    prev = 0
    for eachLine in open(file_name, "rb"):
        prev = zlib.crc32(eachLine, prev)
    return "%X" % (prev & 0xFFFFFFFF)

def random_tag():
    """Get a random tag."""
    return str(uuid.uuid4()).split('-')[0]
