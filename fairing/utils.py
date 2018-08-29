import os

def get_image(package_options):
    # TODO: If no image is specified generate a new one, i.e: user/fairing-build
    return "{repo}/{name}:latest".format(
        repo=package_options.repository,
        name=package_options.name
    )

def is_runtime_phase():
    """ Returns wether the code is currently in the runtime or building phase"""
    return os.getenv('FAIRING_RUNTIME', None) != None 
    
def is_running_in_k8s():
    return os.path.isdir('/var/run/secrets/kubernetes.io/')

def get_current_k8s_namespace():
    with open('/var/run/secrets/kubernets.io/serviceaccount/namespace', 'r') as f:
        return f.readline()