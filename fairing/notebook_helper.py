from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import json
import os.path
import re
import ipykernel
import requests
import nbconvert
from fairing.utils import generate_context_tarball
from notebook.notebookapp import list_running_servers
from requests.compat import urljoin

DEFAULT_CONVERTED_FILENAME="app.py"

def get_notebook_name():
    """
    Return the full path of the jupyter notebook.
    """
    kernel_id = re.search('kernel-(.*).json',
                          ipykernel.connect.get_connection_file()).group(1)
    servers = list_running_servers()
    for ss in servers:
        response = requests.get(urljoin(ss['url'], 'api/sessions'),
                                params={'token': ss.get('token', '')})
        for nn in json.loads(response.text):
            if nn['kernel']['id'] == kernel_id:
                full_path = nn['notebook']['path']
                return os.path.basename(full_path)

def is_in_notebook():
    try:
        ipykernel.get_connection_info()
    except RuntimeError:
        return False
    return True

def export_notebook_to_tar_gz(notebook_file, output_filename, converted_filename=DEFAULT_CONVERTED_FILENAME):
    if notebook_file is None:
        notebook_file = get_notebook_name()
    exporter = nbconvert.PythonExporter()
    contents, _ = exporter.from_filename(notebook_file)
    with open(converted_filename, "w+") as f:
        f.write(contents)
    generate_context_tarball(converted_filename, output_filename)
