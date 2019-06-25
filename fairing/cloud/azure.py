import json
import logging
import os
import base64
import tarfile

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.storage import StorageManagementClient
from azure.mgmt.storage.models import StorageAccountCreateParameters
from azure.mgmt.storage.models import Sku
from azure.mgmt.storage.models import SkuName
from azure.mgmt.storage.models import Kind
from azure.storage.file import FileService
from fairing.constants import constants
from fairing.kubernetes.manager import KubeManager
from kubernetes import client
from pathlib import Path
from shutil import rmtree


logger = logging.getLogger(__name__)

# Helper class to uplaod files to Azure Files
class AzureFileUploader(object):
    def __init__(self, namespace):
        credentials, subscription_id = get_azure_credentials(namespace)
        self.storage_client = StorageManagementClient(credentials, subscription_id)
    
    # Upload the files and dirs in a tar.gz file to a dir in a shared folder in Azure Files
    def upload_to_share(self,
                        region,
                        resource_group_name,
                        storage_account_name,
                        share_name,
                        dir_name,
                        tar_gz_file_to_upload):
        
        logging.info(f"Uploading contents of '{tar_gz_file_to_upload}' to 'https://{storage_account_name}.file.core.windows.net/{share_name}/{dir_name}'")
        
        self.create_storage_account_if_not_exists(region, resource_group_name, storage_account_name)        
        storage_account_name, storage_key = self.get_storage_credentials(resource_group_name, storage_account_name)
        share_service = FileService(account_name=storage_account_name, account_key=storage_key)        
        self.create_share_if_not_exists(share_service, share_name)
        share_service.create_directory(share_name, dir_name)
        self.upload_tar_gz_contents(share_service, share_name, dir_name, tar_gz_file_to_upload)
        
        return storage_account_name, storage_key
        
    def create_storage_account_if_not_exists(self, region, resource_group_name, storage_account_name):
        storage_accounts = self.storage_client.storage_accounts.list_by_resource_group(resource_group_name)
        storage_account = next(filter(lambda storage_account: storage_account.name == storage_account_name, storage_accounts), None)       
        if (storage_account is None):
            # Creation should succeed even if the storage account exists, but if it exists I get error "The property 'isHnsEnabled' was specified in the input, but it cannot be updated.".
            logging.info(f"Creating Azure Storage account '{storage_account_name}' in Resource Group '{resource_group_name}'")
            storage_async_operation = self.storage_client.storage_accounts.create(
                resource_group_name,
                storage_account_name,
                StorageAccountCreateParameters(
                    sku=Sku(name=SkuName.standard_ragrs),
                    kind=Kind.storage,
                    location=region
                )
            )
            storage_async_operation.result()
    
    def get_storage_credentials(self, resource_group_name, storage_account_name):
        storage_keys = self.storage_client.storage_accounts.list_keys(resource_group_name, storage_account_name)
        storage_keys = {v.key_name: v.value for v in storage_keys.keys}
        
        return storage_account_name, storage_keys['key1']
    
    def create_share_if_not_exists(self, share_service, share_name):                        
        shares = share_service.list_shares()
        share = next(filter(lambda share: share.name == share_name, shares), None)      
        if (share is None):
            share_service.create_share(share_name)
    
    def upload_tar_gz_contents(self, share_service, share_name, dir_name, tar_gz_file):
        local_dir = Path(f'{tar_gz_file}_contents')
        cloud_dir = Path(dir_name)
        self.uncompress_tar_gz_file(tar_gz_file, local_dir)

        for path in local_dir.glob('**/*'):
            local_path = Path(path)
            cloud_relative_path = cloud_dir / path.relative_to(local_dir)

            if local_path.is_dir():
                share_service.create_directory(share_name, cloud_relative_path)
            else:
                share_service.create_file_from_path(share_name, cloud_relative_path.parents[0], cloud_relative_path.name, local_path)

        self.delete_uncompressed_files(local_dir)
        
    def uncompress_tar_gz_file(self, tar_gz_file, target_dir):        
        tar = tarfile.open(tar_gz_file, 'r:gz')
        tar.extractall(path=target_dir)
        tar.close()
    
    def delete_uncompressed_files(self, target_dir):
        rmtree(target_dir)

# Get credentials for a service principal which has permissions to create or access the storage account for Azure Files
def get_azure_credentials(namespace):
    secret_name = constants.AZURE_CREDS_SECRET_NAME
    if not KubeManager().secret_exists(secret_name, namespace):
        raise Exception(f"Secret '{secret_name}' not found in namespace '{namespace}'")
        
    v1 = client.CoreV1Api()
    secret = v1.read_namespaced_secret(secret_name, namespace)
    secret_base64 = list(secret.data.values())[0]
    secret_json = base64.b64decode(secret_base64).decode('utf-8')
    credentials = json.loads(secret_json)
    sp_credentials = ServicePrincipalCredentials(
        client_id = credentials['clientId'],
        secret = credentials['clientSecret'],
        tenant = credentials['tenantId']) 
    subscription_id = credentials['subscriptionId']
    return sp_credentials, subscription_id        

# Create a secret with the credentials to access the storage account for Azure Files
def create_storage_creds_secret(namespace, context_hash, storage_account_name, storage_key):
    secret_name = constants.AZURE_STORAGE_CREDS_SECRET_NAME_PREFIX + context_hash.lower()
    logging.info(f"Creating secret '{secret_name}' in namespace '{namespace}'")
    secret = client.V1Secret(
        metadata = client.V1ObjectMeta(name=secret_name),
        string_data={
            'azurestorageaccountname': storage_account_name,
            'azurestorageaccountkey': storage_key
        })
    v1 = client.CoreV1Api()
    v1.create_namespaced_secret(namespace, secret)
        
# Delete the secret with the credentials to access the storage account for Azure Files
def delete_storage_creds_secret(namespace, context_hash):
    secret_name = constants.AZURE_STORAGE_CREDS_SECRET_NAME_PREFIX + context_hash.lower()
    logging.info(f"Deleting secret '{secret_name}' from namespace '{namespace}'")
    v1 = client.CoreV1Api()
    v1.delete_namespaced_secret(secret_name, namespace)
    
# Verify that we are working with an Azure Container Registry
def is_acr_registry(registry):    
    return registry.endswith('.azurecr.io')

# Mount Docker config so the pod can access Azure Container Registry
def add_acr_config(kube_manager, pod_spec, namespace):
    secret_name = constants.AZURE_ACR_CREDS_SECRET_NAME
    if not kube_manager.secret_exists(secret_name, namespace):
        raise Exception(f"Secret '{secret_name}' not found in namespace '{namespace}'")
        
    volume_mount=client.V1VolumeMount(
            name='acr-config', mount_path='/kaniko/.docker/', read_only=True)

    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    items = [client.V1KeyToPath(key='.dockerconfigjson', path='config.json')]
    volume=client.V1Volume(
            name='acr-config',
            secret=client.V1SecretVolumeSource(secret_name=secret_name, items=items))

    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]
        
# Mount Azure Files shared folder so the pod can access its files with a local path
def add_azure_files(kube_manager, pod_spec, namespace):
    context_hash = pod_spec.containers[0].args[1].split(':')[-1]
    secret_name = constants.AZURE_STORAGE_CREDS_SECRET_NAME_PREFIX + context_hash.lower()
    if not kube_manager.secret_exists(secret_name, namespace):
        raise Exception(f"Secret '{secret_name}' not found in namespace '{namespace}'")
        
    volume_mount=client.V1VolumeMount(
        name='azure-files', mount_path='/mnt/azure/', read_only=True)
                         
    if pod_spec.containers[0].volume_mounts:
        pod_spec.containers[0].volume_mounts.append(volume_mount)
    else:
        pod_spec.containers[0].volume_mounts = [volume_mount]

    volume=client.V1Volume(
            name='azure-files',
            azure_file=client.V1AzureFileVolumeSource(secret_name=secret_name, share_name=constants.AZURE_FILES_SHARED_FOLDER))
                         
    if pod_spec.volumes:
        pod_spec.volumes.append(volume)
    else:
        pod_spec.volumes = [volume]
        
