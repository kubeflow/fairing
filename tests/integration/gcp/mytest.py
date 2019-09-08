import os
import pytest

from tests.integration.helpers import run_notebook_test


def test_example_xgb_synthetic():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/xgboost_synthetic/build-train-deploy.ipynb"
    notebook_abs_path = os.path.normpath(
        os.path.join(file_dir, notebook_rel_path))
    expected_messages = [
        "Model export success", #KF training
        "Prediction endpoint: http", #create endpoint success
    ]
    parameters = {
        "NAMESPACE": "kubeflow"
    }
    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)

def test_xgboost_highlevel_apis_gke():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis.ipynb"
    notebook_abs_path = os.path.normpath(
        os.path.join(file_dir, notebook_rel_path))
    expected_messages = [
        "Model export success: trained_ames_model.dat", #KF training
        "Prediction endpoint: http", #create endpoint success
    ]
    parameters = {
        "FAIRING_BACKEND": "KubeflowGKEBackend"
    }
    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)
