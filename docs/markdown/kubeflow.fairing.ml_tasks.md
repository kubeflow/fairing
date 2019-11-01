# kubeflow.fairing.ml_tasks package

## Submodules

## kubeflow.fairing.ml_tasks.tasks module


#### class kubeflow.fairing.ml_tasks.tasks.BaseTask(entry_point, base_docker_image=None, docker_registry=None, input_files=None, backend=None, pod_spec_mutators=None)
Bases: `object`

Base class for handling high level ML tasks.


* **Parameters**

    
    * **entry_point** – An object or reference to the source code that has to be deployed.


    * **base_docker_image** – Name of the base docker image that should be used as a base image
    when building a new docker image as part of an ML task deployment.


    * **docker_registry** – Docker registry to store output docker images.


    * **input_files** – list of files that needs to be packaged along with the entry point.
    E.g. local python modules, trained model weigths, etc.



#### class kubeflow.fairing.ml_tasks.tasks.PredictionEndpoint(model_class, base_docker_image=None, docker_registry=None, input_files=None, backend=None, service_type='ClusterIP', pod_spec_mutators=None)
Bases: `kubeflow.fairing.ml_tasks.tasks.BaseTask`

Create a prediction endpoint.


### create()
Create prediction endpoint.


### delete()
Delete prediction endpoint.


### predict_nparray(data, feature_names=None)
Return the prediction result.


* **Parameters**

    
    * **data** – Data to be predicted.


    * **feature_names** – Feature extracted from data (Default value = None)



#### class kubeflow.fairing.ml_tasks.tasks.TrainJob(entry_point, base_docker_image=None, docker_registry=None, input_files=None, backend=None, pod_spec_mutators=None)
Bases: `kubeflow.fairing.ml_tasks.tasks.BaseTask`

Create a train job.


### submit()
Submit a train job.

## kubeflow.fairing.ml_tasks.utils module


#### kubeflow.fairing.ml_tasks.utils.guess_preprocessor(entry_point, input_files, output_map)
Preprocessor to use to modify inputs before sending them to docker build


* **Parameters**

    
    * **entry_point** – entry_point which to use


    * **input_files** – input files


    * **output_map** – output



#### kubeflow.fairing.ml_tasks.utils.is_docker_daemon_exists()
To check if docker daemon exists or not.

## Module contents
