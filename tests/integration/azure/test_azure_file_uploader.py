import os

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.storage.models import StorageAccount

from kubeflow.fairing.cloud.azure import AzureFileUploader

STORAGE_ACCOUNT_NAME = os.environ.get('AZURE_STORAGE_ACCOUNT')
RESOURCE_GROUP = os.environ.get('AZURE_RESOURCE_GROUP')
REGION = os.environ.get('AZURE_REGION')

def test_storage_account_creation():
    credentials = ServicePrincipalCredentials(
        client_id=os.environ.get('AZ_CLIENT_ID'),
        secret=os.environ.get('AZ_CLIENT_SECRET'),
        tenant=os.environ.get('AZ_TENANT_ID')
    )
    subscription_id = os.environ.get('AZ_SUBSCRIPTION_ID')
    file_uploader = AzureFileUploader(
        RESOURCE_GROUP, credentials=credentials, subscription_id=subscription_id
    )
    storage_account = file_uploader.create_storage_account_if_not_exists(
        REGION, RESOURCE_GROUP, STORAGE_ACCOUNT_NAME
    )
    assert isinstance(storage_account, StorageAccount)
    assert storage_account.name == STORAGE_ACCOUNT_NAME
