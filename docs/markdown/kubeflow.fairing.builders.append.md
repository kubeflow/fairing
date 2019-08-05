# kubeflow.fairing.builders.append package

## Submodules

## kubeflow.fairing.builders.append.append module


#### class kubeflow.fairing.builders.append.append.AppendBuilder(registry=None, image_name='fairing-job', base_image='gcr.io/kubeflow-images-public/fairing:dev', push=True, preprocessor=None)
Bases: `kubeflow.fairing.builders.base_builder.BaseBuilder`

Builds a docker image by appending a new layer tarball to an existing
base image. Does not require docker and runs in userspace.


* **Parameters**

    
    * **base_image** – Base image to use for the build (default: {constants.DEFAULT_BASE_IMAGE})


    * **image_name** – image name to use for the new image(default: {constants.DEFAULT_IMAGE_NAME})


    * **preprocessor** – Preprocessor{BasePreProcessor} to use to modify inputs
    before sending them to docker build


    * **push** – Whether or not to push the image to the registry



### build()
Will be called when the build needs to start


### timed_push(transport, src, img, dst)
Push image to the registry and log the time spent to the log


* **Parameters**

    
    * **transport** – the http transport to use for sending requests


    * **src** – repo from which to mount blobs


    * **img** – the image to be pushed


    * **dst** – the fully-qualified name of the tag to push


## Module contents
