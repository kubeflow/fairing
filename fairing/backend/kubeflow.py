from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import json
import os
import subprocess
import logging

from fairing.backend.native import NativeBackend

logger = logging.getLogger('fairing')

# This class can contain any specifities related to kubeflow services.
# i.e. if kubeflow provides a TensorBoard CRD we could use it here
class KubeflowBackend(NativeBackend): 
    def stream_logs(self, image_name, image_tag):
        logger.warn('You can check the logs for your job by doing ' \
        '"kubectl logs -f fairing-job-%s-0-chief-0"' % image_tag)