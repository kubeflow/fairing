# Metaparticle applied to ML

### Problem statement

A lot of solutions are appearing to help machine learning model developement benefit from Kubernetes' scalability and agility.
The currently best known solution for that is [Kubeflow](https://github.com/kubeflow/kubeflow/). 

Among other things, Kubeflow aims to help with the training and serving phases for those ML models.

However, to benefit from this, a ML researcher/data scientist (DS), needs to either have deep knowledge in docker, kubernetes and it's ecosystem (ksonnet etc.), or hand-off it's  work to an operation team that will be responsible for deploying the trainings on K8s.

While it's becoming more and more accepted that ultimately, developers should be able to interact with a layer of abstraction on top of K8s that is more "native" and scoped to their work (and thus not need to learn K8s deeply), this is even more important for DS that are even less familiar with the container space than the average developer.

### Typical workflow

* A DS generally begins exploration using either Jupyter notebooks, or python scripts. The first few trainings will be relatively fast (smaller dataset) and ran only one at a time.
* If primary results are interesting, a DS will then want to do hyperparameter sweeping to find the combination with the best performance. Since the exploration space can be very large, it is fundamental than many trainings run in parallel (that is the main reason why Kubernetes is interesting for training).
* For large models, distributed training (multiple VMs for a single training) might be needed.
* This trainings need to be monitored using tools such as TensorBoard
* Once a model is deemed good enough, it will then be deployed in production to serve predictions (inference). Compared to training, inference does not go through the "backward propagation" step, and so it is a different code flow.

#### Specific pain points

* Knowledge of docker, kubectl and ksonnet is needed.
* Jupyter notebooks cannot be used for non-interactive training (hyperparameter search, distributed training etc.)
* Conversion from Jupyter notebooks to .py files is cumbersome, but needed.
* Hyperparameters distribution need to be express in yaml format, which is very rigid and doesn't allow everything.
* Setting up Tensorboard in kubernetes to monitor a job running in another pod is not straightforward
* Once the training phase is done, moving to inference needs inclusion of a web server (e.g flask), and distributed system considerations (replicas, load balancing etc.)


## Metaml

Metaml is a python library using metaparticle and exposing simple interfaces that feel natural to data scientists and does not require extensive knowledge of the Kubernetes ecosystem.

### Training with hyperparameter tuning

The `@Train` decorator is used to describe how to train the model.

This decorator will have several basic arguments to tune the training:
* `parallelism` and `completions`: How many trainings should be run in parallel and how many in total. If `completions` is not defined, then `completions = parallelism`
* `hyper_parameters`: A generator function that will be called once for each training. This function should generate different values for each hyperparameters that a user want to explore.
* `tensorboard`: Wheter a tensorboard instance should also be started to monitor the training

```python
def get_hyperparameters():
  yield {
    'learning_rate': random.normalvariate(0.5, 0.5),
    'hidden_layer_size': np.random.choice([128, 256, 512], 1),
    'dropout': random.normalvariate(0.85, 0.10)
  }

@Train(settings={
    'parallelism' = 4,
    'hyper_parameters'= get_hyperparameters(),
    'tensorboard' = True
  },
  package={
    'repository': 'docker.io/your-docker-user-goes-here', 
    'name': 'my-image',
    'publish': True
  })
def train_model(learning_rate, hidden_layer_size, dropout):
  // Training logic
  ...
```

`@Train` will call metaparticle's `@Containerize` function, creating multiple `jobs`.
It will also create a metaparticle `service` for Tensorboard if requested.


### Distributed Training

For distributed training, a user could specify how many parameter servers and workers are needed using the `distributed_settings` property.

This should 

```python
@Train(settings={
    'hyper_parameters'= get_hyperparameters(),
    'parallelism' = 4,
    'tensorboard' = True,
    'distributed_settings': {
      'ps': 2,
      'workers': 5
    }
  },
  package={
    'repository': 'docker.io/your-docker-user-goes-here', 
    'name': 'my-image',
    'publish': True
  })
```

### Serving

The `@Serving` decorator would be used for inference.
This decorator would automatically implement a flask web server and forward all requests to the decorated method.
Metaparticle `@Containerize` decorator would then ben called 
`url`, `port` and `replicas` are optional, and default to `/predict`, `80` and `1` respectively.

```python

@Serve(settings={
    'url': '/predict',
    'port': 80,
    'replicas': 2   
  },
  package={
    'repository': 'docker.io/your-docker-user-goes-here', 
    'name': 'my-image',
    'publish': True
  })
def serve(input):
  // serving logic
  ...
```

### Additional possibilities

* Data input/output (needs exploration):
  * `@DataIn(type='AzureBlob', 'mycontainer/some/dataset')`
  * `@DataOut(type='AzureBlob', 'mycontainer/some/model')`
* Moving from Jupyter notebooks to python scripts is cumbersome. Could These decorators be directly used in Jupyter notebooks, and automatically convert from `.ipynb` to `.py` (using `jupyter nbconvert`) and then deploy to K8s?
  * The notebooks would either need to be structured in a very specific way, or we need to find a way to save and restore the state of the kernel to deal with global variables and such

### Changes needed in metaparticle

* How can metaparticle allow usage of CRDs? For distributed training we would need to use Kubeflow's `TfJob` CRD for example.

