from metaml.backend.kubeflow import KubeflowBackend
from metaml.backend.native import NativeBackend

Kubeflow = 'kubeflow'
Native = 'native'

def get_backend(backend):
    if backend == Kubeflow:
        return KubeflowBackend()
    if backend == Native:
        return NativeBackend()