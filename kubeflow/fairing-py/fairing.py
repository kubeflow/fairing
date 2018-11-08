#!/usr/bin/env python

# Copyright 2018 The Kubeflow Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os.path
import re
import ipykernel
import requests

from requests.compat import urljoin
from notebook.notebookapp import list_running_servers
from nbconvert.preprocessors import Preprocessor
from traitlets.config import Config

import nbconvert
import tarfile
from subprocess import run, PIPE

annotation = 'kubeflow/training'

class AnnotationPreprocessor(Preprocessor):
    def check_cell_conditions(self, cell):
        return annotation in cell.source

    def preprocess(self, nb, resources):
        nb.cells = [cell for cell in nb.cells if self.check_cell_conditions(cell)]
        return nb, resources

# https://github.com/jupyter/notebook/issues/1000#issuecomment-359875246
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
                relative_path = nn['notebook']['path']
                return os.path.join(ss['notebook_dir'], relative_path)


def convert_to_python(notebook_file):
    print("Converting notebook...")
    c = Config()
    c.PythonExporter.preprocessors = [AnnotationPreprocessor]
    exporter = nbconvert.PythonExporter(config=c)
    script, _ = exporter.from_filename(notebook_file)
    return script

def gen_tarball(contents):
    tar_name = "/tmp/output.tar"
    tmpfile = "/tmp/notebook.py"
    with open(tmpfile, "w+") as f:
        f.write(contents)
    with tarfile.open(tar_name, "w:gz") as tar:
        tar.add(tmpfile, filter=reset_tar_mtime)
    return tar_name

def reset_tar_mtime(tarinfo):
    tarinfo.mtime = 0
    return tarinfo

def build_image(base_image="tensorflow/tensorflow:1.11.0-gpu", dst_image=""):
    notebook_name = get_notebook_name()
    source = convert_to_python(notebook_name)
    output_tar = gen_tarball(source)
    print("Starting build...")
    cmd = ["fairing", "build", "--layer-file", output_tar, "--base-image", base_image, "--dst-image", dst_image]
    res = run(cmd, stdout=PIPE)
    print(res.stdout.decode('utf-8'))

