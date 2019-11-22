from kubeflow import fairing
import os
import sys

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
NOTEBOOK_PATH = os.path.join(os.path.dirname(__file__), 'test_notebook.ipynb')


def run_full_notebook_submission(capsys, notebook_file, expected_result,
                                 deployer='job', builder='docker',
                                 namespace='default'):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'python:{}'.format(py_version)
    fairing.config.set_builder(
        builder, base_image=base_image, registry=DOCKER_REGISTRY)
    fairing.config.set_deployer(deployer, namespace=namespace)

    requirements_file = os.path.relpath(
        os.path.join(os.path.dirname(__file__), 'requirements.txt'))
    fairing.config.set_preprocessor('full_notebook', notebook_file=notebook_file,
                                    output_map={requirements_file: '/app/requirements.txt'})

    fairing.config.run()
    captured = capsys.readouterr()
    assert expected_result in captured.out


def test_full_notebook_job(capsys):
    run_full_notebook_submission(capsys, NOTEBOOK_PATH, 'Hello World',
                                 deployer='job')


def test_full_notebook_tfjob(capsys):
    run_full_notebook_submission(capsys, NOTEBOOK_PATH, 'Hello World',
                                 deployer='tfjob', namespace='kubeflow-fairing')
