import re
from unittest.mock import patch
from kubernetes import client

from kubeflow import fairing
from kubeflow.fairing.deployers.gcp.gcpserving import GCPServingDeployer
from kubeflow.fairing.deployers.gcp.gcp import GCPJob


def create_test_pod_spec():
    return client.V1PodSpec(
        containers=[client.V1Container(
            name='model',
            image='test-image'
        )]
    )


def test_fairing_user_agent_in_http_requests_gcpjob_deploy_api(httpmock, capsys):
    with patch('httplib2.Http', new=httpmock) as mock_http:  # pylint:disable=unused-variable
        job = GCPJob()
        job.deploy(create_test_pod_spec())
        captured = capsys.readouterr()
        expected_pattern = r'HTTPMock url:https://ml.googleapis.* user-agent:kubeflow-fairing/{}'\
                           .format(fairing.__version__)
        print(captured.out)
        assert len(re.findall(expected_pattern, captured.out)) > 0  # pylint:disable=len-as-condition


def test_fairing_user_agent_in_http_requests_gcpserving_deploy_api(httpmock, capsys):
    with patch('httplib2.Http', new=httpmock) as mock_http:  # pylint:disable=unused-variable
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')
        deployer.deploy(None)
        captured = capsys.readouterr()
        expected_pattern = r'HTTPMock url:https://ml.googleapis.* user-agent:kubeflow-fairing/{}'\
                           .format(fairing.__version__)
        print(captured.out)
        assert len(re.findall(expected_pattern, captured.out)) > 0  # pylint:disable=len-as-condition
