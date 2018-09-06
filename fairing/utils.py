import os
import uuid

def get_image_full(repository, name, tag):
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