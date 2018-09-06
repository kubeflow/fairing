from fairing.backend.kubeflow import KubeflowBackend
from fairing.backend.native import NativeBackend

Kubeflow = 'kubeflow'
Native = 'native'

def get_backend(backend):
    if backend == Kubeflow:
        return KubeflowBackend()
    if backend == Native:
        return NativeBackend()