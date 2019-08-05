# kubeflow.fairing.backends package

## Submodules

## kubeflow.fairing.backends.backends module


#### class kubeflow.fairing.backends.backends.AWSBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.KubernetesBackend`

Use to create a builder instance and create a deployer to be used with a traing job
or a serving job for the AWS backend.


### get_builder(preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None)
Creates a builder instance with right config for AWS


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this job


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images


    * **needs_deps_installation** – need depends on installation(Default value = True)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value =None)



### get_serving_deployer(model_class, service_type='ClusterIP', pod_spec_mutators=None)
Creates a deployer to be used with a serving job for AWS


* **Parameters**

    
    * **model_class** – the name of the class that holds the predict function.


    * **service_type** – service type (Default value = ‘ClusterIP’)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



### get_training_deployer(pod_spec_mutators=None)
Creates a deployer to be used with a training job for AWS


* **Parameters**

    **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



* **Returns**

    job for handle all the k8s’ template building for a training



#### class kubeflow.fairing.backends.backends.AzureBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.KubernetesBackend`

Use to create a builder instance and create a deployer to be used with a traing job or
a serving job for the Azure backend.


### get_builder(preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None)
Creates a builder instance with right config for Azure


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this job


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images


    * **needs_deps_installation** – need depends on installation(Default value = True)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value =None)



#### class kubeflow.fairing.backends.backends.BackendInterface()
Bases: `object`

Backend interface.
Creating a builder instance or a deployer to be used with a traing job or a serving job
for the given backend.
And get the approriate base container or docker registry for the current environment.


### get_base_contanier()
Returns the approriate base container for the current environment


* **Returns**

    base image



### abstract get_builder(preprocessor, base_image, registry)
Creates a builder instance with right config for the given backend


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this builder


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images



* **Raises**

    **NotImplementedError** – not implemented exception



### get_docker_registry()
Returns the approriate docker registry for the current environment


* **Returns**

    None



### abstract get_serving_deployer(model_class)
Creates a deployer to be used with a serving job


* **Parameters**

    **model_class** – the name of the class that holds the predict function.



* **Raises**

    **NotImplementedError** – not implemented exception



### abstract get_training_deployer(pod_spec_mutators=None)
Creates a deployer to be used with a training job


* **Parameters**

    **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value = None)



* **Raises**

    **NotImplementedError** – not implemented exception



#### class kubeflow.fairing.backends.backends.GCPManagedBackend(project_id=None, region=None, training_scale_tier=None)
Bases: `kubeflow.fairing.backends.backends.BackendInterface`

Use to create a builder instance and create a deployer to be used with a traing job
or a serving job for the GCP.


### get_builder(preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None)
Creates a builder instance with right config for GCP


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this job


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images


    * **needs_deps_installation** – need depends on installation(Default value = True)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value =None)



### get_docker_registry()
Returns the approriate docker registry for GCP


* **Returns**

    docker registry



### get_serving_deployer(model_class, pod_spec_mutators=None)
Creates a deployer to be used with a serving job for GCP


* **Parameters**

    
    * **model_class** – the name of the class that holds the predict function.


    * **service_type** – service type (Default value = ‘ClusterIP’)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



### get_training_deployer(pod_spec_mutators=None)
Creates a deployer to be used with a training job for GCP


* **Parameters**

    **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



* **Returns**

    job for handle all the k8s’ template building for a training



#### class kubeflow.fairing.backends.backends.GKEBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.KubernetesBackend`

Use to create a builder instance and create a deployer to be used with a traing job
or a serving job for the GKE backend.
And get the approriate docker registry for GKE.


### get_builder(preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None)
Creates a builder instance with right config for GKE


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this job


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images


    * **needs_deps_installation** – need depends on installation(Default value = True)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value =None)



### get_docker_registry()
Returns the approriate docker registry for GKE


* **Returns**

    docker registry



### get_serving_deployer(model_class, service_type='ClusterIP', pod_spec_mutators=None)
Creates a deployer to be used with a serving job for GKE


* **Parameters**

    
    * **model_class** – the name of the class that holds the predict function.


    * **service_type** – service type (Default value = ‘ClusterIP’)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



### get_training_deployer(pod_spec_mutators=None)
Creates a deployer to be used with a training job for GKE


* **Parameters**

    **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



* **Returns**

    job for handle all the k8s’ template building for a training



#### class kubeflow.fairing.backends.backends.KubeflowAWSBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.AWSBackend`

Kubeflow for AWS backend refer to AWSBackend


#### class kubeflow.fairing.backends.backends.KubeflowAzureBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.AzureBackend`

Kubeflow for Azure backend refer to AzureBackend


#### class kubeflow.fairing.backends.backends.KubeflowBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.KubernetesBackend`

Kubeflow backend refer to KubernetesBackend


#### class kubeflow.fairing.backends.backends.KubeflowGKEBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.GKEBackend`

Kubeflow for GKE backend refer to GKEBackend


#### class kubeflow.fairing.backends.backends.KubernetesBackend(namespace=None, build_context_source=None)
Bases: `kubeflow.fairing.backends.backends.BackendInterface`

Use to create a builder instance and create a deployer to be used with a traing job or
a serving job for the Kubernetes.


### get_builder(preprocessor, base_image, registry, needs_deps_installation=True, pod_spec_mutators=None)
Creates a builder instance with right config for the given Kubernetes


* **Parameters**

    
    * **preprocessor** – Preprocessor to use to modify inputs


    * **base_image** – Base image to use for this job


    * **registry** – Registry to push image to. Example: gcr.io/kubeflow-images


    * **needs_deps_installation** – need depends on installation(Default value = True)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    e.g. fairing.cloud.gcp.add_gcp_credentials_if_exists
    This can used to set things like volumes and security context.
    (Default value =None)



### get_serving_deployer(model_class, service_type='ClusterIP', pod_spec_mutators=None)
Creates a deployer to be used with a serving job for the Kubernetes


* **Parameters**

    
    * **model_class** – the name of the class that holds the predict function.


    * **service_type** – service type (Default value = ‘ClusterIP’)


    * **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



### get_training_deployer(pod_spec_mutators=None)
Creates a deployer to be used with a training job for the Kubernetes


* **Parameters**

    **pod_spec_mutators** – list of functions that is used to mutate the podsspec.
    (Default value = None)



* **Returns**

    job for handle all the k8s’ template building for a training


## Module contents
