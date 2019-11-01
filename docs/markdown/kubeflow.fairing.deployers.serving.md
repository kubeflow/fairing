# kubeflow.fairing.deployers.serving package

## Submodules

## kubeflow.fairing.deployers.serving.serving module


#### class kubeflow.fairing.deployers.serving.serving.Serving(serving_class, namespace=None, runs=1, labels=None, service_type='ClusterIP', pod_spec_mutators=None)
Bases: `kubeflow.fairing.deployers.job.job.Job`

Serves a prediction endpoint using Kubernetes deployments and services


### delete()
delete the deployed service


### deploy(pod_spec)
deploy a seldon-core REST service


* **Parameters**

    **pod_spec** – pod spec for the service



### generate_deployment_spec(pod_template_spec)
generate deployment spec(V1Deployment)


* **Parameters**

    **pod_template_spec** – pod spec template



### generate_service_spec()
generate service spec(V1ServiceSpec)

## Module contents
