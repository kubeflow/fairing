from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import open
from future import standard_library
standard_library.install_aliases()

import shutil
import sys
import os
import logging
import tempfile
logger = logging.getLogger('fairing')

from fairing.constants import constants

def write_dockerfile(
    destination=constants.DEFAULT_GENERATED_DOCKERFILE_FILENAME,
    path_prefix=constants.DEFAULT_DEST_PREFIX,
    dockerfile_path=None,
    base_image=None):
    content = '\n'.join([
        "FROM {}".format(base_image),
        "ENV FAIRING_RUNTIME 1",
        "COPY {PATH_PREFIX} {PATH_PREFIX}".format(PATH_PREFIX=path_prefix),
        "RUN if [ -e requirements.txt ]; then pip install --no-cache -r requirements.txt; fi"
    ])
    with open(destination, 'w') as f:
        f.write(content)
    return destination
