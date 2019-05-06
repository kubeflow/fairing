"""Tests for GCPServing Deployer."""

import pytest
import json
import httplib2
from unittest.mock import patch

from fairing.deployers.gcp.gcpserving import GCPServingDeployer
from googleapiclient.errors import HttpError


def create_http_error(error_code, message):
    error_content = json.dumps({
        'error': {
            'code': error_code,
            'message': message,
            'details': message
        }
    }).encode()
    headers = {'status': str(error_code), 'content-type': 'application/json'}
    response = httplib2.Response(headers)
    response.reason = message
    return HttpError(response, error_content)


# Test that deployment fails if an invalid model request is provided.
def test_invalid_model_request(capsys):
    with patch('fairing.deployers.gcp.gcpserving.discovery.build') as mock_ml:
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')

    (mock_ml.return_value.projects.return_value.models.return_value
     .get.side_effect) = create_http_error(
        error_code=400, message='invalid request')

    deployer.deploy(None)

    captured = capsys.readouterr()
    assert 'Error retrieving the model' in captured.out


# Test that deployment fails if an invalid model creation request is provided.
def test_invalid_model_creation(capsys):
    with patch('fairing.deployers.gcp.gcpserving.discovery.build') as mock_ml:
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')

    (mock_ml.return_value.projects.return_value.models.return_value
     .get.return_value.execute.return_value) = None
    (mock_ml.return_value.projects.return_value.models.return_value
     .create.side_effect) = create_http_error(
        error_code=400, message='invalid request')

    deployer.deploy(None)

    captured = capsys.readouterr()
    assert 'Error creating the model' in captured.out


# Test that a new model is created if not found.
def test_model_creation_with_404():
    with patch('fairing.deployers.gcp.gcpserving.discovery.build') as mock_ml:
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')

    (mock_ml.return_value.projects.return_value.models.return_value
     .get.side_effect) = create_http_error(
         error_code=404, message='model not found')

    deployer.deploy(None)
    args, kwargs = (mock_ml.return_value.projects.return_value
                    .models.return_value.create.call_args)

    assert kwargs['parent'] == 'projects/test_project'
    assert kwargs['body'] == {'name': 'test_model'}


# Test that deployment fails if an invalid version creation request is provided.
def test_invalid_version_creation(capsys):
    with patch('fairing.deployers.gcp.gcpserving.discovery.build') as mock_ml:
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')

    (mock_ml.return_value.projects.return_value.models.return_value
     .versions.return_value.create.return_value
     .execute.side_effect) = create_http_error(
        error_code=400, message='invalid request')

    deployer.deploy(None)

    captured = capsys.readouterr()
    assert 'Error creating the version' in captured.out


# Test that a new version is created with the correct arguments.
def test_valid_creation(capsys):
    with patch('fairing.deployers.gcp.gcpserving.discovery.build') as mock_ml:
        deployer = GCPServingDeployer(
            project_id='test_project', model_dir='test_model_dir',
            model_name='test_model', version_name='test_version')

    deployer.deploy(None)
    args, kwargs = (mock_ml.return_value.projects.return_value.models
                    .return_value.versions.return_value.create.call_args)

    assert kwargs['parent'] == 'projects/test_project/models/test_model'
    assert kwargs['body'] == {
        'name': 'test_version',
        'deploymentUri': 'test_model_dir',
        'python_version': '3.5',
        'runtime_version': '1.13'
    }

    captured = capsys.readouterr()
    assert 'Version submitted successfully' in captured.out

def test_fairing_user_agent_in_http_requests_gcpserving_build_api():
    class HTTPMock:        
        def request(self, *args, **kwargs):
            print(args, kwargs)
            raise RuntimeError(args[3]['user-agent'])            
    with patch('httplib2.Http', new=HTTPMock) as mock_http:
        with pytest.raises(RuntimeError) as excinfo:
            deployer = GCPServingDeployer(
                project_id='test_project', model_dir='test_model_dir',
                model_name='test_model', version_name='test_version')
        assert "kubeflow-fairing/0.5.2" == str(excinfo.value)

def test_fairing_user_agent_in_http_requests_gcpserving_deploy_api(ml_api_spec_response):
    """
    google python client builds classes for a service by getting an api spec
    for the service dynamically. Here we are testing if the user agent is properly
    set for the deploy call that comes after the google python client builds classes
    for the service.

    Since both calls (to get api spec and deploy model) uses the same http instance
    we need to mock a sequence of http calls. The first call should return a api spec and
    the second call throws an error that used to check the validity of the test.
    """
    class HTTPMock:
        first_request = True        
        def request(self, *args, **kwargs):
            if HTTPMock.first_request:
                HTTPMock.first_request = False
                return ml_api_spec_response
            else:
                raise RuntimeError(args[3]['user-agent'])           
    with patch('httplib2.Http', new=HTTPMock) as mock_http:
        deployer = GCPServingDeployer(
                project_id='test_project', model_dir='test_model_dir',
                model_name='test_model', version_name='test_version')
        with pytest.raises(RuntimeError) as excinfo:
            deployer.deploy(None)
        assert "kubeflow-fairing/0.5.2" == str(excinfo.value)
