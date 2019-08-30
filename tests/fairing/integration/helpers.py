import tempfile
import logging
import os
import papermill

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
        # TODO (karthikv2k): find a better way to test notebook execution success
        if not expected_message in actual_output:
            logger.error(actual_output)
            assert False, "Unable to find from output: " + expected_message
