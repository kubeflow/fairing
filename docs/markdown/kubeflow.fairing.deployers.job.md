# kubeflow.fairing.deployers.job package

## Submodules

## kubeflow.fairing.deployers.job.job module


#### class kubeflow.fairing.deployers.job.job.Job(namespace=None, runs=1, output=None, cleanup=True, labels=None, job_name='fairing-job-', stream_log=True, deployer_type='job', pod_spec_mutators=None, annotations=None)
Bases: `kubeflow.fairing.deployers.deployer.DeployerInterface`

Handle all the k8s’ template building for a training


### create_resource()
create job


### deploy(pod_spec)
deploy the training job using k8s client lib


* **Parameters**

    **pod_spec** – pod spec of deployed training job



### do_cleanup()
clean up the pods after job finished


### generate_deployment_spec(pod_template_spec)
Generate a V1Job initialized with correct completion and

    parallelism (for HP search) and with the provided V1PodTemplateSpec


* **Parameters**

    **pod_template_spec** – V1PodTemplateSpec



### generate_pod_template_spec(pod_spec)
Generate a V1PodTemplateSpec initiazlied with correct metadata

    and with the provided pod_spec


* **Parameters**

    **pod_spec** – pod spec



### get_logs()
get logs from the deployed job


### set_anotations(annotations)

### set_labels(labels, deployer_type)
set labels for the pods of a deployed job


* **Parameters**

    
    * **labels** – dictionary of labels {label_name:label_value}


    * **deployer_type** – deployer type name


## Module contents
