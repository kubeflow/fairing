import tarfile
import os
import posixpath
from pathlib import Path

from kubeflow.fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessor
from kubeflow.fairing.preprocessors.converted_notebook import ConvertNotebookPreprocessorWithFire
from kubeflow.fairing.preprocessors.converted_notebook import FilterIncludeCell
from kubeflow.fairing.constants.constants import DEFAULT_DEST_PREFIX

NOTEBOOK_PATH = os.path.relpath(
    os.path.join(os.path.dirname(__file__), 'test_notebook.ipynb'))
CONVERTED_NOTEBOOK_PATH = NOTEBOOK_PATH.replace(".ipynb", ".py")


def test_preprocess():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    files = preprocessor.preprocess()
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    os.remove(converted_notebook_path)
    assert Path(converted_notebook_path) in files


def test_overwrite_file_for_multiple_runs():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    files = preprocessor.preprocess()
    files_overwrite = preprocessor.preprocess()
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    os.remove(converted_notebook_path)
    assert files == files_overwrite


def test_get_command():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    preprocessor.preprocess()
    command = preprocessor.get_command()
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    conv_notebook_context_path = posixpath.join(
        DEFAULT_DEST_PREFIX, converted_notebook_path)
    expected_command = 'python {}'.format(conv_notebook_context_path)
    os.remove(converted_notebook_path)
    assert command == expected_command.split()


def test_context_tar_gz():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH)
    context_file, _ = preprocessor.context_tar_gz()
    tar = tarfile.open(context_file)
    relative_path_prefix = posixpath.relpath(DEFAULT_DEST_PREFIX, "/")
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    notebook_context_path = posixpath.join(
        relative_path_prefix, converted_notebook_path)
    tar_notebook = tar.extractfile(tar.getmember(notebook_context_path))
    os.remove(converted_notebook_path)
    assert "print('Hello World')" in tar_notebook.read().decode()


def test_filter_include_cell():
    preprocessor = ConvertNotebookPreprocessor(notebook_file=NOTEBOOK_PATH,
                                               notebook_preprocessor=FilterIncludeCell)
    context_file, _ = preprocessor.context_tar_gz()
    tar = tarfile.open(context_file)
    relative_path_prefix = posixpath.relpath(DEFAULT_DEST_PREFIX, "/")
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    notebook_context_path = posixpath.join(
        relative_path_prefix, converted_notebook_path)
    tar_notebook = tar.extractfile(tar.getmember(notebook_context_path))
    tar_notebook_text = tar_notebook.read().decode()
    os.remove(converted_notebook_path)
    assert "print('This cell includes fairing:include-cell')" in tar_notebook_text


def test_context_tar_gz_with_fire():
    preprocessor = ConvertNotebookPreprocessorWithFire(
        notebook_file=NOTEBOOK_PATH)
    context_file, _ = preprocessor.context_tar_gz()
    tar = tarfile.open(context_file)
    relative_path_prefix = posixpath.relpath(DEFAULT_DEST_PREFIX, "/")
    converted_notebook_path = posixpath.join(os.path.dirname(
        NOTEBOOK_PATH), os.path.basename(preprocessor.executable))
    notebook_context_path = posixpath.join(
        relative_path_prefix, converted_notebook_path)
    tar_notebook = tar.extractfile(tar.getmember(notebook_context_path))
    tar_notebook_text = tar_notebook.read().decode()
    os.remove(converted_notebook_path)
    assert "fire.Fire(None)" in tar_notebook_text
