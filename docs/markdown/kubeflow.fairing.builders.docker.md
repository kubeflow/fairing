# kubeflow.fairing.builders.docker package

## Submodules

## kubeflow.fairing.builders.docker.docker module


#### class kubeflow.fairing.builders.docker.docker.DockerBuilder(registry=None, image_name='fairing-job', base_image='gcr.io/kubeflow-images-public/fairing:dev', preprocessor=None, push=True, dockerfile_path=None)
Bases: `kubeflow.fairing.builders.base_builder.BaseBuilder`

A builder using the local Docker client


### build()
Runs the build


### publish()
push the docker image to the docker registry

## Module contents
