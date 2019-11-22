import json
import os.path
import ipykernel
import re
from notebook.notebookapp import list_running_servers
import requests
from requests.compat import urljoin


def get_notebook_name(): #pylint:disable=inconsistent-return-statements
    """Return the full path of the jupyter notebook. """
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
    """To check is in notenook or not. """

    try:
        ipykernel.get_connection_info()
    # Temporary fix for #84
    # TODO: remove blanket Exception catching after fixing #84
    except Exception:
        return False
    return True
