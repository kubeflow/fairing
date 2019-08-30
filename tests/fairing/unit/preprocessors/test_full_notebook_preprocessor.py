import tarfile
import os

from kubeflow.fairing.preprocessors.full_notebook import FullNotebookPreProcessor

NOTEBOOK_PATH = os.path.relpath(
    os.path.join(os.path.dirname(__file__), 'test_notebook.ipynb'))


def test_preprocess():
    preprocessor = FullNotebookPreProcessor(notebook_file=NOTEBOOK_PATH)
    files = preprocessor.preprocess()
    assert NOTEBOOK_PATH in files


def test_get_command():
    preprocessor = FullNotebookPreProcessor(notebook_file=NOTEBOOK_PATH)
    command = preprocessor.get_command()
    expected_command = 'papermill {} fairing_output_notebook.ipynb --log-output'.format(
        NOTEBOOK_PATH)
    assert command == expected_command.split()


def test_context_tar_gz():
    preprocessor = FullNotebookPreProcessor(notebook_file=NOTEBOOK_PATH)
    context_file, _ = preprocessor.context_tar_gz()
    tar = tarfile.open(context_file)

    notebook_context_path = os.path.join('app/', NOTEBOOK_PATH)
    tar_notebook = tar.extractfile(tar.getmember(notebook_context_path))
    assert 'Hello World' in tar_notebook.read().decode()
