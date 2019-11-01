# kubeflow.fairing.kubernetes package

## Submodules

## kubeflow.fairing.kubernetes.manager module


#### class kubeflow.fairing.kubernetes.manager.KubeManager()
Bases: `object`

Handles communication with Kubernetes’ client.


### create_deployment(namespace, deployment)
Create an V1Deployment in the specified namespace.


* **Parameters**

    
    * **namespace** – The custom resource


    * **deployment** – Deployment body to create



* **Returns**

    object: Created V1Deployments.



### create_job(namespace, job)
Creates a V1Job in the specified namespace.


* **Parameters**

    
    * **namespace** – The resource


    * **job** – Job defination as kubernetes



* **Returns**

    object: Created Job.



### create_kfserving(namespace, kfservice)
Create the provided KFServing in the specified namespace.


* **Parameters**

    
    * **namespace** – The custom resource


    * **kfservice** – The kfservice body



* **Returns**

    object: Created KFService.



### create_secret(namespace, secret)
Create secret in the specified namespace.


* **Parameters**

    
    * **namespace** – The custom resource


    * **secret** – The secret body



* **Returns**

    object: Created secret.



### create_tf_job(namespace, job)
Create the provided TFJob in the specified namespace.
The TFJob version is defined in TF_JOB_VERSION in fairing.constants.
The version TFJob need to be installed before creating the TFJob.


* **Parameters**

    
    * **namespace** – The custom resource


    * **job** – The JSON schema of the Resource to create



* **Returns**

    object: Created TFJob.



### delete_deployment(name, namespace)
Delete an existing model deployment and relinquish all resources associated.


* **Parameters**

    
    * **name** – The deployment name


    * **namespace** – The custom resource



* **Returns**

    obje   deployment.



### delete_job(name, namespace)
Delete the specified job and related pods.


* **Parameters**

    
    * **name** – The job name


    * **namespace** – The resource



* **Returns**

    object: the deleted job.



### delete_kfserving(name, namespace)
Delete the provided KFServing in the specified namespace.


* **Parameters**

    
    * **name** – The custom object


    * **namespace** – The custom resource



* **Returns**

    object: The deleted kfservice.



### delete_tf_job(name, namespace)
Delete the provided TFJob in the specified namespace.


* **Parameters**

    
    * **name** – The custom object


    * **namespace** – The custom resource



* **Returns**

    object: The deleted TFJob.



### get_service_external_endpoint(name, namespace, selectors=None)
Get the service external endpoint as [http://ip_or_hostname:5000/predict](http://ip_or_hostname:5000/predict).


* **Parameters**

    
    * **name** – The sevice name


    * **namespace** – The custom resource


    * **selectors** – A selector to restrict the list of returned objects by their labels.


    * **Defaults** – to everything



* **Returns**

    str: the service external endpoint.



### log(name, namespace, selectors=None, container='', follow=True)
Get log of the specified pod.


* **Parameters**

    
    * **name** – The pod name


    * **namespace** – The custom resource


    * **selectors** – A selector to restrict the list of returned objects by their labels.


    * **Defaults** – to everything


    * **container** – The container for which to stream logs.


    * **if** – there is one container in the pod


    * **follow** – True or False (Default value = True)



* **Returns**

    str: logs of the specified pod.



### secret_exists(name, namespace)
Check if the secret exists in the specified namespace.


* **Parameters**

    
    * **name** – The secret name


    * **namespace** – The custom resource.



* **Returns**

    bool: True if the secret exists, otherwise return False.


## kubeflow.fairing.kubernetes.utils module


#### kubeflow.fairing.kubernetes.utils.get_resource_mutator(cpu=None, memory=None)
The mutator for getting the resource setting for pod spec.

The useful example:
[https://github.com/kubeflow/fairing/blob/master/examples/train_job_api/main.ipynb](https://github.com/kubeflow/fairing/blob/master/examples/train_job_api/main.ipynb)


* **Parameters**

    
    * **cpu** – Limits and requests for CPU resources (Default value = None)


    * **memory** – Limits and requests for memory (Default value = None)



* **Returns**

    object: The mutator function for setting cpu and memory in pod spec.



#### kubeflow.fairing.kubernetes.utils.mounting_pvc(pvc_name, pvc_mount_path='/mnt')
The function for pod_spec_mutators to mount persistent volume claim.


* **Parameters**

    
    * **pvc_name** – The name of persistent volume claim


    * **pvc_mount_path** – Path for the persistent volume claim mounts to.



* **Returns**

    object: function for mount the pvc to pods.


## Module contents
