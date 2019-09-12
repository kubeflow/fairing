import os
import logging

from ..helpers import run_notebook_test

logger = logging.getLogger(__name__)

def update_parameters(parameters, parameter_name):
    if parameter_name in os.environ:
        parameters[parameter_name] = os.environ[parameter_name]

def test_xgboost_highlevel_apis():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis.ipynb"
    notebook_abs_path = os.path.normpath(os.path.join(file_dir, notebook_rel_path))
    expected_messages = [
        "Model export success: trained_ames_model.dat",
        "Deploying the endpoint.",
        "Prediction endpoint: http",
        "Deleting the endpoint."
    ]
    parameters = {
        "FAIRING_BACKEND": "KubeflowAzureBackend"
    }
    update_parameters(parameters, "DOCKER_REGISTRY")
    update_parameters(parameters, "AZURE_RESOURCE_GROUP")
    update_parameters(parameters, "AZURE_STORAGE_ACCOUNT")
    update_parameters(parameters, "AZURE_REGION")
    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)
