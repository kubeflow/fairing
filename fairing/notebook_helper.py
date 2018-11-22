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
from notebook.notebookapp import list_running_servers
from requests.compat import urljoin

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
