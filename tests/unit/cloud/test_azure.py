import pytest
import json
import base64
import uuid

from unittest.mock import patch
from fairing.kubernetes.manager import KubeManager
from kubernetes import client
from azure.common.credentials import ServicePrincipalCredentials

from fairing.cloud.azure import get_azure_credentials

TEST_CLIENT_ID = str(uuid.uuid4())
TEST_CLIENT_SECRET = str(uuid.uuid4())
TEST_TENANT_ID = str(uuid.uuid4())
TEST_SUBSCRIPTION_ID = str(uuid.uuid4())

class MockSecret(object):
    def __init__(self):
        self.data = self
        self.values = self.secret
    def secret(self):
        secret_dict = {
            'clientId': TEST_CLIENT_ID,
            'clientSecret': TEST_CLIENT_SECRET,
            'tenantId': TEST_TENANT_ID,
            'subscriptionId': TEST_SUBSCRIPTION_ID
        }
        return [base64.b64encode(json.dumps(secret_dict).encode())]

# Test that credentials are parsed properly from the Kubernetes secrets.
@patch.object(KubeManager, 'secret_exists')
@patch.object(KubeManager, '__init__')
@patch.object(client.CoreV1Api, 'read_namespaced_secret')
@patch.object(ServicePrincipalCredentials, '__init__')
def test_get_azure_credentials(credentials_init_mock,
                               read_namespaced_secret_mock,
                               manager_init_mock,
                               secret_exists_mock):
    secret_exists_mock.return_value = True
    manager_init_mock.return_value = None
    read_namespaced_secret_mock.return_value = MockSecret()
    credentials_init_mock.return_value = None
    get_azure_credentials('kubeflow')
    credentials_init_mock.assert_called_with(
        client_id=TEST_CLIENT_ID,
        secret=TEST_CLIENT_SECRET,
        tenant=TEST_TENANT_ID
    )
