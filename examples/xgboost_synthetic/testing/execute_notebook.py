import tempfile
import logging
import os
import papermill
#import sys
#import time
#import uuid

'''
import fairing
from fairing.builders.cluster import gcs_context
from fairing.constants import constants

logger = logging.getLogger(__name__)

GCS_PROJECT_ID = fairing.cloud.gcp.guess_project_name()
DOCKER_REGISTRY = 'gcr.io/{}'.format(GCS_PROJECT_ID)
'''
def execute_notebook(notebook_path, parameters=None):
  temp_dir = tempfile.mkdtemp()
  notebook_output_path = os.path.join(temp_dir, "out.ipynb")
  papermill.execute_notebook(notebook_path, notebook_output_path,
                             cwd=os.path.dirname(notebook_path),
                             parameters=parameters,
                             log_output=True)
  return notebook_output_path

def run_notebook_test(notebook_path, expected_messages, parameters=None):
  output_path = execute_notebook(notebook_path, parameters=parameters)
  actual_output = open(output_path, 'r').read()
  for expected_message in expected_messages:
    if not expected_message in actual_output:
      logger.error(actual_output)
      assert False, "Unable to find from output: " + expected_message

'''
def train_fn(msg):
    for _ in range(30):
        time.sleep(0.1)
        print(msg)

def run_submission_with_function_preprocessor(deployer="job", builder="append",
                                              namespace="default", cleanup=False):
    py_version = ".".join([str(x) for x in sys.version_info[0:3]])
    base_image = 'registry.hub.docker.com/library/python:{}'.format(py_version)
    if builder == 'cluster':
        fairing.config.set_builder(builder, base_image=base_image, registry=DOCKER_REGISTRY,
                                   pod_spec_mutators=[
                                       fairing.cloud.gcp.add_gcp_credentials],
                                   context_source=gcs_context.GCSContextSource(
                                       namespace=namespace),
                                   namespace=namespace)
    else:
        fairing.config.set_builder(
            builder, base_image=base_image, registry=DOCKER_REGISTRY)

    expected_result = str(uuid.uuid4())
    fairing.config.set_deployer(deployer, namespace=namespace, cleanup=cleanup,
                                labels={'pytest-id': expected_result})

    remote_train = fairing.config.fn(lambda: train_fn(expected_result))
    remote_train()
    #captured = capsys.readouterr()
    #assert expected_result in captured.out
'''

if __name__ == "__main__":

  #run_submission_with_function_preprocessor(deployer="job")

  FILE_DIR = os.path.dirname(__file__)
  NOTEBOOK_REL_PATH = "../build-train-deploy.ipynb"
  NOTEBOOK_ABS_PATH = os.path.normpath(os.path.join(FILE_DIR, NOTEBOOK_REL_PATH))
  #TBD @jinchihe Add more check pionts for each steps.
  EXPECTED_MGS = [
      "Successfully installed",
      "Model export success: mockup-model.dat",
      "Cluster endpoint: http",
      "\"tensor\":{\"shape\"",
      "'workspace': 'xgboost-synthetic'"
  ]
  run_notebook_test(NOTEBOOK_ABS_PATH, EXPECTED_MGS)
