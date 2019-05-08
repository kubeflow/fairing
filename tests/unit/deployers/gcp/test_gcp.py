import pytest
import re
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

def test_fairing_user_agent_in_http_requests_gcpjob_deploy_api(httpmock, capsys):
    with patch('httplib2.Http', new=httpmock) as mock_http:
        job = GCPJob()
        job.deploy(create_test_pod_spec())
        captured = capsys.readouterr()
        expected_pattern = r'HTTPMock url:https://ml.googleapis.* user-agent:kubeflow-fairing/0.5.2'
        print(captured.out)
        assert len(re.findall(expected_pattern, captured.out)) > 0
