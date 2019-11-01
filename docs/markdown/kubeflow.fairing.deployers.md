# kubeflow.fairing.deployers package

## Subpackages


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


## Submodules

## kubeflow.fairing.deployers.deployer module


#### class kubeflow.fairing.deployers.deployer.DeployerInterface()
Bases: `object`

Deploys a training job to the cluster


### deploy(pod_template_spec)
Deploys the training job


* **Parameters**

    **pod_template_spec** – pod template spec



### abstract get_logs()
Streams the logs for the training job

## Module contents
