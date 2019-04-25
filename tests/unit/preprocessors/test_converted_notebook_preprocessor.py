import pytest
import tarfile
import os
import posixpath
from pathlib import Path

import fairing
from fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessor
from fairing.constants.constants import DEFAULT_DEST_PREFIX

NOTEBOOK_PATH = os.path.relpath(
    os.path.join(os.path.dirname(__file__), 'test_notebook.ipynb'))
CONVERTED_NOTEBOOK_PATH = NOTEBOOK_PATH.replace(".ipynb",".py")

def test_preprocess():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    files = preprocessor.preprocess()
    assert Path(CONVERTED_NOTEBOOK_PATH) in files

def test_get_command():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    preprocessor.preprocess()
    command = preprocessor.get_command()
    conv_notebook_context_path = posixpath.join(DEFAULT_DEST_PREFIX, CONVERTED_NOTEBOOK_PATH)
    expected_command = 'python {}'.format(conv_notebook_context_path)
    print(command)
    assert command == expected_command.split()

def test_context_tar_gz():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    context_file, _ = preprocessor.context_tar_gz()
    tar = tarfile.open(context_file)
    relative_path_prefix = posixpath.relpath(DEFAULT_DEST_PREFIX, "/") 
    notebook_context_path = posixpath.join(relative_path_prefix, CONVERTED_NOTEBOOK_PATH)
    tar_notebook = tar.extractfile(tar.getmember(notebook_context_path))
    assert "print('Hello World')" in tar_notebook.read().decode()
