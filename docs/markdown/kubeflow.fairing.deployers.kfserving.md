# kubeflow.fairing.deployers.kfserving package

## Submodules

## kubeflow.fairing.deployers.kfserving.kfserving module


#### class kubeflow.fairing.deployers.kfserving.kfserving.KFServing(framework, default_model_uri=None, canary_model_uri=None, canary_traffic_percent=0, namespace=None, labels=None, annotations=None, custom_default_spec=None, custom_canary_spec=None, stream_log=True, cleanup=False)
Bases: `kubeflow.fairing.deployers.deployer.DeployerInterface`

Serves a prediction endpoint using Kubeflow KFServing.


### deploy(template_spec)
deploy kfserving endpoint


* **Parameters**

    **template_spec** – template spec



### generate_kfservice()
generate kfserving template


### get_logs()
get log from prediction pod


### set_labels(labels)
set label for deployed prediction


* **Parameters**

    **labels** – dictionary of labels {label_name:label_value}


## Module contents
