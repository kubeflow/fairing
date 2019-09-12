from kubernetes import client
from kubeflow import fairing
from kubeflow.fairing.deployers.gcp.gcp import GCPJob

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
        'jobId': job._job_name, #pylint:disable=protected-access
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
        'jobId': job._job_name, #pylint:disable=protected-access
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
        'jobId': job._job_name, #pylint:disable=protected-access
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
        'jobId': job._job_name, #pylint:disable=protected-access
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
