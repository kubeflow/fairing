# kubeflow.fairing.cloud package

## Submodules

## kubeflow.fairing.cloud.aws module


#### class kubeflow.fairing.cloud.aws.S3Uploader(region)
Bases: `object`

For AWS S3 up load


### create_bucket_if_not_exists(bucket_name)
Create bucket if this bucket not exists


* **Parameters**

    **bucket_name** – Bucket name



### upload_to_bucket(blob_name, bucket_name, file_to_upload)
Upload a file to an S3 bucket


* **Parameters**

    
    * **blob_name** – S3 object name


    * **bucket_name** – Bucket to upload to


    * **file_to_upload** – File to upload



#### kubeflow.fairing.cloud.aws.add_aws_credentials(kube_manager, pod_spec, namespace)
add AWS credential


* **Parameters**

    
    * **kube_manager** – kube manager for handles communication with Kubernetes’ client


    * **pod_spec** – pod spec like volumes and security context


    * **namespace** – The custom resource



#### kubeflow.fairing.cloud.aws.add_aws_credentials_if_exists(kube_manager, pod_spec, namespace)
add AWS credential


* **Parameters**

    
    * **kube_manager** – kube manager for handles communication with Kubernetes’ client


    * **pod_spec** – pod spec like volumes and security context


    * **namespace** – The custom resource



#### kubeflow.fairing.cloud.aws.add_ecr_config(kube_manager, pod_spec, namespace)
add secret


* **Parameters**

    
    * **kube_manager** – kube manager for handles communication with Kubernetes’ client


    * **pod_spec** – pod spec like volumes and security context


    * **namespace** – The custom resource



#### kubeflow.fairing.cloud.aws.create_ecr_registry(registry, repository)
create secret registry


* **Parameters**

    
    * **registry** – registry


    * **repository** – repository name



#### kubeflow.fairing.cloud.aws.guess_account_id()
Get account id


#### kubeflow.fairing.cloud.aws.is_ecr_registry(registry)
verify secrte registy


* **Parameters**

    **registry** – registry


## kubeflow.fairing.cloud.azure module


#### class kubeflow.fairing.cloud.azure.AzureFileUploader(namespace, credentials=None, subscription_id=None)
Bases: `object`


### create_share_if_not_exists(share_service, share_name)

### create_storage_account_if_not_exists(region, resource_group_name, storage_account_name)
Creates the storage account if it does not exist.

In either case, returns the StorageAccount class that matches the given arguments.


### delete_uncompressed_files(target_dir)

### get_storage_credentials(resource_group_name, storage_account_name)

### uncompress_tar_gz_file(tar_gz_file, target_dir)

### upload_tar_gz_contents(share_service, share_name, dir_name, tar_gz_file)

### upload_to_share(region, resource_group_name, storage_account_name, share_name, dir_name, tar_gz_file_to_upload)

#### kubeflow.fairing.cloud.azure.add_acr_config(kube_manager, pod_spec, namespace)

#### kubeflow.fairing.cloud.azure.add_azure_files(kube_manager, pod_spec, namespace)

#### kubeflow.fairing.cloud.azure.create_storage_creds_secret(namespace, context_hash, storage_account_name, storage_key)

#### kubeflow.fairing.cloud.azure.delete_storage_creds_secret(namespace, context_hash)

#### kubeflow.fairing.cloud.azure.get_azure_credentials(namespace)

#### kubeflow.fairing.cloud.azure.get_plain_secret_value(secret_data, key)

#### kubeflow.fairing.cloud.azure.is_acr_registry(registry)
## kubeflow.fairing.cloud.docker module


#### kubeflow.fairing.cloud.docker.add_docker_credentials(kube_manager, pod_spec, namespace)

#### kubeflow.fairing.cloud.docker.add_docker_credentials_if_exists(kube_manager, pod_spec, namespace)

#### kubeflow.fairing.cloud.docker.create_docker_secret(kube_manager, namespace)

#### kubeflow.fairing.cloud.docker.get_docker_secret()
## kubeflow.fairing.cloud.gcp module


#### class kubeflow.fairing.cloud.gcp.GCSUploader(credentials_file=None)
Bases: `object`


### get_or_create_bucket(bucket_name)

### upload_to_bucket(blob_name, bucket_name, file_to_upload)

#### kubeflow.fairing.cloud.gcp.add_gcp_credentials(kube_manager, pod_spec, namespace)
Note: This method will be deprecated soon and will become unavailable by 1.0.
All future access will use Workload Identity.


#### kubeflow.fairing.cloud.gcp.add_gcp_credentials_if_exists(kube_manager, pod_spec, namespace)

#### kubeflow.fairing.cloud.gcp.get_default_docker_registry()

#### kubeflow.fairing.cloud.gcp.guess_project_name(credentials_file=None)
## kubeflow.fairing.cloud.storage module


#### class kubeflow.fairing.cloud.storage.GCSStorage()
Bases: `kubeflow.fairing.cloud.storage.Storage`


### copy_cmd(src_url, dst_url, recursive=True)
gets a command to copy files from/to remote storage from/to local FS


### exists(url)
checks if the url exists in the given storage


#### class kubeflow.fairing.cloud.storage.Storage()
Bases: `object`


### abstract copy_cmd(src_url, dst_url, recursive=True)
gets a command to copy files from/to remote storage from/to local FS


### abstract exists(url)
checks if the url exists in the given storage


#### kubeflow.fairing.cloud.storage.get_storage_class(url)

#### kubeflow.fairing.cloud.storage.lookup_storage_class(url)
## Module contents
