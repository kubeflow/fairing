import os
import pytest

from ..helpers import run_notebook_test

@pytest.mark.skip(reason="GCPManaged backend needs to take build context as input")
def test_xgboost_highlevel_apis_gcp_managed():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis.ipynb"
    notebook_abs_path = os.path.normpath(
        os.path.join(file_dir, notebook_rel_path))
    expected_messages = [
        "Model export success: trained_ames_model.dat",  # KF training
        "Access job logs at the following URL:",  # GCP managed submission success
        "Prediction endpoint: http",  # create endpoint success
    ]
    parameters = {
        "FAIRING_BACKEND": "GCPManagedBackend"
    }
    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)

# TODO(abhishek): The invocation of the prediction endpoint fails possibly
# because the endpoint may not be ready when the prediction calls are made.
# Temporarily disabling this test until I find the fix.
#def test_xgboost_highlevel_apis_gke():
#    file_dir = os.path.dirname(__file__)
#    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis.ipynb"
#    notebook_abs_path = os.path.normpath(
#        os.path.join(file_dir, notebook_rel_path))
#    expected_messages = [
#        "Model export success: trained_ames_model.dat", #KF training
#        "Prediction endpoint: http", #create endpoint success
#    ]
#    parameters = {
#        "FAIRING_BACKEND": "KubeflowGKEBackend"
#    }
#    run_notebook_test(notebook_abs_path, expected_messages, parameters=parameters)


def test_lightgbm():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/lightgbm/distributed-training.ipynb"
    notebook_abs_path = os.path.normpath(
        os.path.join(file_dir, notebook_rel_path))
    expected_messages = [
        "Copying gs://fairing-lightgbm/regression-example/regression.train.weight",
        "[LightGBM] [Info] Finished initializing network",  # dist training setup
        "[LightGBM] [Info] Iteration:10, valid_1 l2 : 0.2",
        "[LightGBM] [Info] Finished training",
        "Prediction mean: 0.5",
        ", count: 500"
    ]
    run_notebook_test(notebook_abs_path, expected_messages)
