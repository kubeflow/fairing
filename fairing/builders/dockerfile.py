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
logger = logging.getLogger('fairing')

from fairing.notebook_helper import get_notebook_name, is_in_notebook
   
def get_exec_file_name():
    exec_file = sys.argv[0]
    slash_ix = exec_file.find('/')
    if slash_ix != -1:
        exec_file = exec_file[slash_ix + 1:]
    return exec_file

def get_command():
    exec_file = ''
    if is_in_notebook():
        nb_name = get_notebook_name()
        exec_file = nb_name.replace('.ipynb', '.py')
    else:
        exec_file = get_exec_file_name()

    return "CMD python /app/{exec_file}".format(exec_file=exec_file)

def get_default_base_image():
    dev = os.environ.get('FAIRING_DEV', False)
    if dev:
        try:
            uname = os.environ['FAIRING_DEV_DOCKER_USERNAME']
        except KeyError:
            raise KeyError("FAIRING_DEV environment variable is defined but "
                            "FAIRING_DEV_DOCKER_USERNAME is not. Either set "
                            "FAIRING_DEV_DOCKER_USERNAME to your Docker hub username, "
                            "or set FAIRING_DEV to false.")
        return '{uname}/fairing:dev'.format(uname=uname)
    return 'library/python:3.6'

def generate_dockerfile(base_image):
    if base_image is None:
        base_image = get_default_base_image()
    
    all_steps = ['FROM {base}'.format(base=base_image)] + \
                get_mandatory_steps() + \
                [get_command()]

    return '\n'.join(all_steps)

def get_mandatory_steps():
    steps = [
        "ENV FAIRING_RUNTIME 1",
        "RUN pip install fairing",
        "COPY ./ /app/",
        "RUN if [ -e /app/requirements.txt ]; then pip install --no-cache -r /app/requirements.txt; fi"
    ]

    if is_in_notebook():
        nb_name = get_notebook_name()
        steps += [
            "RUN pip install jupyter nbconvert",
            "RUN jupyter nbconvert --to script /app/{}".format(nb_name)
        ]
    return steps

def write_dockerfile(destination='Dockerfile', dockerfile_path=None, base_image=None):
    if dockerfile_path is not None:
        shutil.copy(dockerfile_path, destination)
        return       
    
    content =  generate_dockerfile(base_image)
    with open(destination, 'w+t') as f:
        f.write(content)

