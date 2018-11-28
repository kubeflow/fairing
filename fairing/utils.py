from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import str
from builtins import open
from future import standard_library
standard_library.install_aliases()

import os
import uuid
import tarfile

def get_image_full_name(repository, name, tag):
    return "{base}:{tag}".format(
        base=get_image(repository, name),
        tag=tag
    )

def get_image(repository, name):
    return "{repo}/{name}".format(
        repo=repository,
        name=name
    )

def is_runtime_phase():
    """ Returns wether the code is currently in the runtime or building phase"""
    return os.getenv('FAIRING_RUNTIME', None) != None 
    
def is_running_in_k8s():
    return os.path.isdir('/var/run/secrets/kubernetes.io/')

def get_current_k8s_namespace():
    with open('/var/run/secrets/kubernetes.io/serviceaccount/namespace', 'r') as f:
        return f.readline()

def get_unique_tag():
    id = uuid.uuid4()
    return str(id).split('-')[0]

def get_default_target_namespace():
    if not is_running_in_k8s():
        return 'default'
    return get_current_k8s_namespace()

def generate_context_tarball(src_filename, output_tar_filename):
    with tarfile.open(output_tar_filename, "w:gz") as tar:
        tar.add(src_filename, filter=reset_tar_mtime)

# Reset the mtime on the the tarball for reproducibility
def reset_tar_mtime(tarinfo):
    tarinfo.mtime = 0
    tarinfo.name = os.path.join("/app", tarinfo.name)
    return tarinfo
