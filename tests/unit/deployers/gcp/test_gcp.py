import pytest
import fairing

import httplib2
from kubernetes import client
from fairing.deployers.gcp.gcp import GCPJob
from unittest.mock import patch
from googleapiclient import discovery

PROJECT_ID = fairing.cloud.gcp.guess_project_name()

def create_test_pod_spec():
    return client.V1PodSpec(
        containers=[client.V1Container(
            name='model',
            image='test-image'
        )]
    )

def test_default_params():
    job = GCPJob()
    request = job.create_request_dict(create_test_pod_spec())

    desired = {
        'jobId': job._job_name,
        'trainingInput': {
            'masterConfig': {
                'imageUri': 'test-image'
            },
            'region': 'us-central1'
        }
    }

    assert request == desired

def test_top_level_args():
    job = GCPJob(region='us-west1', scale_tier='BASIC')
    request = job.create_request_dict(create_test_pod_spec())

    desired = {
        'jobId': job._job_name,
        'trainingInput': {
            'masterConfig': {
                'imageUri': 'test-image'
            },
            'region': 'us-west1',
            'scaleTier': 'BASIC'
        }
    }

    assert request == desired

def test_custom_job_config():
    job = GCPJob(job_config={
        'trainingInput': {
            'scaleTier': 'CUSTOM',
            'masterType': 'standard'
        }
    })
    request = job.create_request_dict(create_test_pod_spec())

    desired = {
        'jobId': job._job_name,
        'trainingInput': {
            'masterConfig': {
                'imageUri': 'test-image'
            },
            'region': 'us-central1',
            'scaleTier': 'CUSTOM',
            'masterType': 'standard'
        }
    }

    assert request == desired

def test_top_level_params_override_job_config():
    job = GCPJob(region='us-west1', scale_tier='BASIC', job_config={
        'trainingInput': {
            'region': 'europe-west1',
            'scaleTier': 'PREMIUM_1'
        },
        'labels': {
            'test-key': 'test-value'
        }
    })
    request = job.create_request_dict(create_test_pod_spec())

    desired = {
        'jobId': job._job_name,
        'trainingInput': {
            'masterConfig': {
                'imageUri': 'test-image'
            },
            'region': 'us-west1',
            'scaleTier': 'BASIC'
        },
        'labels': {
            'test-key': 'test-value'
        }
    }

    assert request == desired

def test_fairing_user_agent_in_http_requests_gcpjob_build_api():
    class HTTPMock:        
        def request(self, *args, **kwargs):
            raise RuntimeError(args[3]['user-agent'])            
    with patch('httplib2.Http', new=HTTPMock) as mock_http:
        with pytest.raises(RuntimeError) as excinfo:
            job = GCPJob()
        assert "kubeflow-fairing/0.5.2" == str(excinfo.value)

def test_fairing_user_agent_in_http_requests_gcpjob_deploy_api(ml_api_spec_response):
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
        job = GCPJob()
        with pytest.raises(RuntimeError) as excinfo:
            job.deploy(create_test_pod_spec())
        assert "kubeflow-fairing/0.5.2" == str(excinfo.value)
