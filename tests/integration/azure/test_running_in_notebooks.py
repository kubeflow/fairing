import tempfile
import papermill
import os
import logging

logger = logging.getLogger(__name__)

def execute_notebook(notebook_path, parameters=None):
    temp_dir = tempfile.mkdtemp()
    notebook_output_path = os.path.join(temp_dir, "out.ipynb")

    papermill.execute_notebook(notebook_path, notebook_output_path,
                               cwd=os.path.dirname(notebook_path),
                               parameters=parameters)
    return notebook_output_path

def run_notebook_test(notebook_path, expected_messages, parameters=None):
    output_path = execute_notebook(notebook_path, parameters=parameters)
    actual_output = open(output_path, 'r').read()
    # TODO (karthikv2k): use something like https://github.com/nteract/scrapbook
    # for reading notebooks
    for expected_message in expected_messages:
        if not expected_message in actual_output:
            logger.error(actual_output)
            assert False, "Unable to find from output: " + expected_message

def update_parameters(parameters, parameter_name):
    if parameter_name in os.environ:
        parameters[parameter_name] = os.environ[parameter_name]

def test_xgboost_highlevel_apis():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis-azure.ipynb"
    notebook_abs_path = os.path.normpath(os.path.join(file_dir, notebook_rel_path))
    # TODO (karthikv2k): find a better way to test notebook execution success
    expected_messages = [
        "Model export success: trained_ames_model.dat",
        "Deploying the endpoint.",
        "Prediction endpoint: http",
        "Deleting the endpoint."
    ]
    parameters = dict()
    update_parameters(parameters, "DOCKER_REGISTRY")
    update_parameters(parameters, "AZURE_RESOURCE_GROUP")
    update_parameters(parameters, "AZURE_STORAGE_ACCOUNT")
    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)
