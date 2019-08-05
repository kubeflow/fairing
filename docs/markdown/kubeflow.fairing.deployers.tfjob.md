# kubeflow.fairing.deployers.tfjob package

## Submodules

## kubeflow.fairing.deployers.tfjob.tfjob module


#### class kubeflow.fairing.deployers.tfjob.tfjob.TfJob(namespace=None, worker_count=1, ps_count=0, chief_count=1, runs=1, job_name='fairing-tfjob-', stream_log=True, labels=None, pod_spec_mutators=None, cleanup=False)
Bases: `kubeflow.fairing.deployers.job.job.Job`

Handle all the k8s’ template building to create tensorflow
training job using Kubeflow TFOperator


### create_resource()
create a tfjob training


### generate_deployment_spec(pod_template_spec)
Returns a TFJob template


* **Parameters**

    **pod_template_spec** – template spec for pod



### get_logs()
get logs


### set_container_name(pod_template_spec)
Sets the name of the main container to tensorflow.

    This is required for TfJobs


* **Parameters**

    **pod_template_spec** – spec for pod template


## Module contents
