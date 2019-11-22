import os
from kubeflow.fairing.ml_tasks.tasks import TrainJob, PredictionEndpoint

if os.getenv('FAIRING_RUNTIME', None) is not None:
    from kubeflow.fairing.runtime_config import config
else:
    from kubeflow.fairing.config import config

name = "fairing"

__version__ = "0.7.0"
