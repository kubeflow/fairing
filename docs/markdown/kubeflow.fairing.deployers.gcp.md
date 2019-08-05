# kubeflow.fairing.deployers.gcp package

## Submodules

## kubeflow.fairing.deployers.gcp.gcp module


#### class kubeflow.fairing.deployers.gcp.gcp.GCPJob(project_id=None, region=None, scale_tier=None, job_config=None)
Bases: `kubeflow.fairing.deployers.deployer.DeployerInterface`

Handle submitting training job to GCP.


### create_request_dict(pod_template_spec)
Return the request to be sent to the ML Engine API.


* **Parameters**

    **pod_template_spec** – pod spec template of the training job



### deploy(pod_template_spec)
Deploys the training job


* **Parameters**

    **pod_template_spec** – pod spec template of the training job



### get_logs()
Streams the logs for the training job

## kubeflow.fairing.deployers.gcp.gcpserving module


#### class kubeflow.fairing.deployers.gcp.gcpserving.GCPServingDeployer(model_dir, model_name, version_name, project_id=None, \*\*deploy_kwargs)
Bases: `kubeflow.fairing.deployers.deployer.DeployerInterface`

Handle deploying a trained model to GCP.


### deploy(pod_template_spec)
Deploys the model to Cloud ML Engine.


* **Parameters**

    **pod_template_spec** – pod spec template of training job



### get_logs()
abstract get log

## Module contents
