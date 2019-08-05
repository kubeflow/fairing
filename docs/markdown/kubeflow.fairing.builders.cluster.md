# kubeflow.fairing.builders.cluster package

## Submodules

## kubeflow.fairing.builders.cluster.azurestorage_context module


#### class kubeflow.fairing.builders.cluster.azurestorage_context.StorageContextSource(namespace=None, region=None, resource_group_name=None, storage_account_name=None)
Bases: `kubeflow.fairing.builders.cluster.context_source.ContextSourceInterface`

Azure storage context source


### cleanup()
Cleans up the context after the build is complete


### generate_pod_spec(image_name, push)
Generates a pod spec for building the image in the cluster, pointing to
the prepared build context


* **Parameters**

    **pod_spec** – pod spec



### prepare(context_filename)
Makes the context somehow available for use in the pod spec


### upload_context(context_filename)
## kubeflow.fairing.builders.cluster.cluster module


#### class kubeflow.fairing.builders.cluster.cluster.ClusterBuilder(registry=None, image_name='fairing-job', context_source=None, preprocessor=None, push=True, base_image='gcr.io/kubeflow-images-public/fairing:dev', pod_spec_mutators=None, namespace=None, dockerfile_path=None, cleanup=False)
Bases: `kubeflow.fairing.builders.base_builder.BaseBuilder`

Builds a docker image in a Kubernetes cluster.


### build()
Runs the build

## kubeflow.fairing.builders.cluster.context_source module


#### class kubeflow.fairing.builders.cluster.context_source.ContextSourceInterface()
Bases: `object`

Interface that provides the build context to the in cluster builder


### abstract cleanup()
Cleans up the context after the build is complete


### abstract generate_pod_spec(pod_spec)
Generates a pod spec for building the image in the cluster, pointing to
the prepared build context


* **Parameters**

    **pod_spec** – pod spec



### abstract prepare()
Makes the context somehow available for use in the pod spec

## kubeflow.fairing.builders.cluster.gcs_context module


#### class kubeflow.fairing.builders.cluster.gcs_context.GCSContextSource(gcp_project=None, credentials_file=None, namespace='default')
Bases: `kubeflow.fairing.builders.cluster.context_source.ContextSourceInterface`

Google cloud storage context for docker builder


### cleanup()
Cleans up the context after the build is complete


### generate_pod_spec(image_name, push)
Generates a pod spec for building the image in the cluster, pointing to
the prepared build context


* **Parameters**

    **pod_spec** – pod spec



### prepare(context_filename)
Makes the context somehow available for use in the pod spec


### upload_context(context_filename)
## kubeflow.fairing.builders.cluster.s3_context module


#### class kubeflow.fairing.builders.cluster.s3_context.S3ContextSource(aws_account=None, region=None, bucket_name=None)
Bases: `kubeflow.fairing.builders.cluster.context_source.ContextSourceInterface`

aws S3 context for docker builder


### cleanup()
Cleans up the context after the build is complete


### generate_pod_spec(image_name, push)
Generates a pod spec for building the image in the cluster, pointing to
the prepared build context


* **Parameters**

    **pod_spec** – pod spec



### prepare(context_filename)

* **Parameters**

    **context_filename** – context filename



### upload_context(context_filename)

* **Parameters**

    **context_filename** – context filename


## Module contents
