<<<<<<< HEAD
=======
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

from fairing.backend.kubeflow import KubeflowBackend
from fairing.backend.native import NativeBackend

Kubeflow = 'kubeflow'
Native = 'native'

def get_backend(backend):
    if backend == Kubeflow:
        return KubeflowBackend()
    if backend == Native:
        return NativeBackend()
>>>>>>> master
