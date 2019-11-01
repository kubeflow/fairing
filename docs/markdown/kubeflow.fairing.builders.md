# kubeflow.fairing.builders package

## Subpackages


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


## Submodules

## kubeflow.fairing.builders.base_builder module


#### class kubeflow.fairing.builders.base_builder.BaseBuilder(registry=None, image_name=None, base_image='gcr.io/kubeflow-images-public/fairing:dev', push=True, preprocessor=None, dockerfile_path=None)
Bases: `kubeflow.fairing.builders.builder.BuilderInterface`

A builder using the local Docker client


### build()
Runs the build


### full_image_name(tag)
Retrun the full image name


* **Parameters**

    **tag** – the new tag for the image



### generate_pod_spec()
This method should return a V1PodSpec with the correct image set.
This is also where the builder should set the environment variables
and volume/volumeMounts that it may need to work

## kubeflow.fairing.builders.builder module


#### class kubeflow.fairing.builders.builder.BuilderInterface()
Bases: `object`


### abstract build()
Will be called when the build needs to start


### abstract generate_pod_spec()
This method should return a V1PodSpec with the correct image set.
This is also where the builder should set the environment variables
and volume/volumeMounts that it may need to work

## kubeflow.fairing.builders.dockerfile module


#### kubeflow.fairing.builders.dockerfile.write_dockerfile(docker_command=None, destination=None, path_prefix='/app/', base_image=None, install_reqs_before_copy=False)
Generate dockerfile accoding to the parameters


* **Parameters**

    
    * **docker_command** – string, CMD of the dockerfile (Default value = None)


    * **destination** – string, destination folder for this dockerfile (Default value = None)


    * **path_prefix** – string, WORKDIR (Default value = constants.DEFAULT_DEST_PREFIX)


    * **base_image** – string, base image, example: gcr.io/kubeflow-image


    * **install_reqs_before_copy** – whether to install the prerequisites (Default value = False)


## Module contents
