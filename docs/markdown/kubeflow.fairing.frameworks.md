# kubeflow.fairing.frameworks package

## Submodules

## kubeflow.fairing.frameworks.lightgbm module


#### kubeflow.fairing.frameworks.lightgbm.execute(config, docker_registry, base_image='gcr.io/kubeflow-fairing/lightgbm:latest', namespace=None, stream_log=True, cores_per_worker=None, memory_per_worker=None, pod_spec_mutators=None)
Runs the LightGBM CLI in a single pod in user’s Kubeflow cluster.
Users can configure it to be a train, predict, and other supported tasks
by using the right config.
Please refere [https://github.com/microsoft/LightGBM/blob/master/docs/Parameters.rst](https://github.com/microsoft/LightGBM/blob/master/docs/Parameters.rst)
for more information on config options.


* **Parameters**

    
    * **config** – config entries


    * **docker_registry** – docker registry name


    * **base_image** – base image (Default value = “gcr.io/kubeflow-fairing/lightgbm:latest”)


    * **namespace** – k8s namespace (Default value = None)


    * **stream_log** – should that stream log? (Default value = True)


    * **cores_per_worker** – number of cores per worker (Default value = None)


    * **memory_per_worker** – memory value per worker (Default value = None)


    * **pod_spec_mutators** – pod spec mutators (Default value = None)



#### kubeflow.fairing.frameworks.lightgbm.generate_context_files(config, config_file_name, num_machines)
generate context files


* **Parameters**

    
    * **config** – config entries


    * **config_file_name** – config file name


    * **num_machines** – number of machines


## kubeflow.fairing.frameworks.lightgbm_dist_training_init module

## kubeflow.fairing.frameworks.utils module


#### kubeflow.fairing.frameworks.utils.get_config_value(config, field_names)
get value for a config entry


* **Parameters**

    
    * **config** – 


    * **field_names** – 



#### kubeflow.fairing.frameworks.utils.init_lightgbm_env(config_file, mlist_file)
initialize env for lightgbm


* **Parameters**

    
    * **config_file** – path to config path


    * **mlist_file** – path to file to write ip list



#### kubeflow.fairing.frameworks.utils.load_properties_config_file(config_file)
load config from a file


* **Parameters**

    **config_file** – config file path



#### kubeflow.fairing.frameworks.utils.nslookup(hostname, retries=600)
Does nslookup for the hostname and returns the IPs for it.


* **Parameters**

    
    * **hostname** – hostname to be looked up


    * **retries** – Number of retries before failing. In autoscaled cluster,
    it might take upto 10mins to create a new node so the default value
    is set high.(Default value = 600)



#### kubeflow.fairing.frameworks.utils.parse_cluster_spec_env()
parse cluster spec env variables


#### kubeflow.fairing.frameworks.utils.save_properties_config_file(config, file_name=None)
save config into a file


* **Parameters**

    
    * **config** – dictionary of give configs


    * **file_name** – path to config file(Default value = None)



#### kubeflow.fairing.frameworks.utils.scrub_fields(config, filed_names)
scrub fields in config


* **Parameters**

    
    * **config** – config spec


    * **filed_names** – name of fields



#### kubeflow.fairing.frameworks.utils.update_config_file(file_name, field_name, new_value)
update config file


* **Parameters**

    
    * **file_name** – file name


    * **field_name** – field name


    * **new_value** – new value to be added/updated



#### kubeflow.fairing.frameworks.utils.write_ip_list_file(file_name, ips, port=None)
write list of ips into a file


* **Parameters**

    
    * **file_name** – fine name


    * **ips** – list of ips


    * **port** – default port(Default value = None)


## Module contents
