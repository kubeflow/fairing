import json
import os
import subprocess
from fairing.backend.native import NativeBackend

# This class can contain any specifities related to kubeflow services.
# i.e. if kubeflow provides a TensorBoard CRD we could use it here
class KubeflowBackend(NativeBackend): pass