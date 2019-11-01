# kubeflow.fairing package

## Subpackages


* kubeflow.fairing.backends package


    * Submodules


    * kubeflow.fairing.backends.backends module


    * Module contents


* kubeflow.fairing.builders package


    * Subpackages


        * kubeflow.fairing.builders.append package


            * Submodules


            * kubeflow.fairing.builders.append.append module


            * Module contents


        * kubeflow.fairing.builders.cluster package


            * Submodules


            * kubeflow.fairing.builders.cluster.azurestorage_context module


            * kubeflow.fairing.builders.cluster.cluster module


            * kubeflow.fairing.builders.cluster.context_source module


            * kubeflow.fairing.builders.cluster.gcs_context module


            * kubeflow.fairing.builders.cluster.s3_context module


            * Module contents


        * kubeflow.fairing.builders.docker package


            * Submodules


            * kubeflow.fairing.builders.docker.docker module


            * Module contents


    * Submodules


    * kubeflow.fairing.builders.base_builder module


    * kubeflow.fairing.builders.builder module


    * kubeflow.fairing.builders.dockerfile module


    * Module contents


* kubeflow.fairing.cloud package


    * Submodules


    * kubeflow.fairing.cloud.aws module


    * kubeflow.fairing.cloud.azure module


    * kubeflow.fairing.cloud.docker module


    * kubeflow.fairing.cloud.gcp module


    * kubeflow.fairing.cloud.storage module


    * Module contents


* kubeflow.fairing.constants package


    * Submodules


    * kubeflow.fairing.constants.constants module


    * Module contents


* kubeflow.fairing.deployers package


    * Subpackages


        * kubeflow.fairing.deployers.gcp package


            * Submodules


            * kubeflow.fairing.deployers.gcp.gcp module


            * kubeflow.fairing.deployers.gcp.gcpserving module


            * Module contents


        * kubeflow.fairing.deployers.job package


            * Submodules


            * kubeflow.fairing.deployers.job.job module


            * Module contents


        * kubeflow.fairing.deployers.kfserving package


            * Submodules


            * kubeflow.fairing.deployers.kfserving.kfserving module


            * Module contents


        * kubeflow.fairing.deployers.serving package


            * Submodules


            * kubeflow.fairing.deployers.serving.serving module


            * Module contents


        * kubeflow.fairing.deployers.tfjob package


            * Submodules


            * kubeflow.fairing.deployers.tfjob.tfjob module


            * Module contents


    * Submodules


    * kubeflow.fairing.deployers.deployer module


    * Module contents


* kubeflow.fairing.frameworks package


    * Submodules


    * kubeflow.fairing.frameworks.lightgbm module


    * kubeflow.fairing.frameworks.lightgbm_dist_training_init module


    * kubeflow.fairing.frameworks.utils module


    * Module contents


* kubeflow.fairing.functions package


    * Submodules


    * kubeflow.fairing.functions.function_shim module


    * Module contents


* kubeflow.fairing.kubernetes package


    * Submodules


    * kubeflow.fairing.kubernetes.manager module


    * kubeflow.fairing.kubernetes.utils module


    * Module contents


* kubeflow.fairing.ml_tasks package


    * Submodules


    * kubeflow.fairing.ml_tasks.tasks module


    * kubeflow.fairing.ml_tasks.utils module


    * Module contents


* kubeflow.fairing.notebook package


    * Submodules


    * kubeflow.fairing.notebook.notebook_util module


    * Module contents


* kubeflow.fairing.preprocessors package


    * Submodules


    * kubeflow.fairing.preprocessors.base module


    * kubeflow.fairing.preprocessors.converted_notebook module


    * kubeflow.fairing.preprocessors.full_notebook module


    * kubeflow.fairing.preprocessors.function module


    * Module contents


## Submodules

## kubeflow.fairing.config module


#### class kubeflow.fairing.config.Config()
Bases: `object`


### deploy(pod_spec)
deploy the job


* **Parameters**

    **pod_spec** – pod spec of the job



### fn(fn)
function


* **Parameters**

    **fn** – return func that set the preprocessorr and run



### get_builder(preprocessor)
get the builder


* **Parameters**

    **preprocessor** – preprocessor function



### get_deployer()
get deployer


### get_preprocessor()
get the preprocessor


### reset()
reset the preprocessor, builder_name and deployer name


### run()
run the pipeline for job


### set_builder(name='append', \*\*kwargs)
set the builder


* **Parameters**

    **name** – builder name (Default value = DEFAULT_BUILDER)



### set_deployer(name='job', \*\*kwargs)
set the deployer


* **Parameters**

    **name** – deployer name (Default value = DEFAULT_DEPLOYER)



### set_preprocessor(name=None, \*\*kwargs)

* **Parameters**

    **name** – preprocessor name(Default value = None)


## kubeflow.fairing.http_utils module


#### kubeflow.fairing.http_utils.configure_http_instance(http=None)
Configure http instance to modify the request headers to append or modify user-agent.


* **Parameters**

    **http** – Body of googleapiclient (Default value = None)



* **Returns**

    object: Configurated http contents.


## kubeflow.fairing.runtime_config module


#### class kubeflow.fairing.runtime_config.RuntimeConfig()
Bases: `object`

A passthrough config shim that runs in the fairing runtime


### fn(func)

### get_builder()

### get_deployer(\*\*kwargs)

### get_preprocessor()

### reset()

### run()

### set_builder(name, \*\*kwargs)

### set_deployer(name, \*\*kwargs)

### set_preprocessor(name, \*\*kwargs)
## kubeflow.fairing.utils module


#### kubeflow.fairing.utils.crc(file_name)
Compute a running Cyclic Redundancy Check checksum.


* **Parameters**

    **file_name** – The file name that’s for crc checksum.



#### kubeflow.fairing.utils.get_current_k8s_namespace()
Get the current namespace of kubernetes.


#### kubeflow.fairing.utils.get_default_target_namespace()
Get the default target namespace, if running in the kubernetes cluster,
will be current namespace, Otherwiase, will be “default”.


#### kubeflow.fairing.utils.get_image(repository, name)
Get the full image name by integrating repository and image name.


* **Parameters**

    
    * **repository** – The name of repository


    * **name** – The short image name



* **Returns**

    str: Full image name, format: repo/name.



#### kubeflow.fairing.utils.is_running_in_k8s()
Check if running in the kubernetes cluster.


#### kubeflow.fairing.utils.random_tag()
Get a random tag.

## Module contents
