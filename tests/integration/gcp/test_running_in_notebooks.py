import pytest
import fairing
import sys
import io
import tempfile
import random
import papermill
import os


def execute_notebook(notebook_path):
    temp_dir = tempfile.mkdtemp()
    notebook_output_path = os.path.join(temp_dir,"out.ipynb")

    papermill.execute_notebook(notebook_path, notebook_output_path, cwd=os.path.dirname(notebook_path))
    return notebook_output_path

def run_notebook_test(notebook_path, expected_messages):
    output_path = execute_notebook(notebook_path)
    actual_output = open(output_path, 'r').read()
    # TODO (karthikv2k): use something like https://github.com/nteract/scrapbook
    # for reading notebooks 
    for expected_message in expected_messages:
        assert expected_message in actual_output

def test_xgboost_highlevel_apis():
    file_dir = os.path.dirname(__file__)
    notebook_rel_path = "../../../examples/prediction/xgboost-high-level-apis.ipynb"
    notebook_abs_path = os.path.normpath(os.path.join(file_dir, notebook_rel_path))
    # TODO (karthikv2k): find a better way to test notebook execution success
    expected_messages = [
        "Model export success: trained_ames_model.dat", #KF training
        "Access job logs at the following URL:", #GCP managed submission success
        "Prediction endpoint: http", #create endpoint success
    ]
    run_notebook_test(notebook_abs_path, expected_messages)
