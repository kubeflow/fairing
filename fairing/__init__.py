import os

if os.getenv('FAIRING_RUNTIME', None) is not None:
    from fairing.runtime_config import config
else:
    from fairing.config import config

name = "fairing"
from .ml_tasks.tasks import TrainJob, PredictionEndpoint

__version__ = "0.5.3"
