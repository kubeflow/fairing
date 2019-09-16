import os
from .ml_tasks.tasks import TrainJob, PredictionEndpoint

if os.getenv('FAIRING_RUNTIME', None) is not None:
    from .runtime_config import config
else:
    from .config import config

name = "fairing"

__version__ = "0.6.0"
