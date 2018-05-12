:warning:  **This project is an experiment** :warning:

# MetaMLs

Easily train and serve ML models on Kubernetes, directly from your python code.
This projects uses [Metaparticle](https://github.com/wbuchwalter/metaparticle-ast) behind the scene.

## Overview

MetaML allows you to express how you want your model to be trained and served using native python decorators.  

```python
@Train(
    package={'name': 'some_image_name', 'repository': 'some_docker_repo', 'publish': True},
    strategy=HyperparameterTuning({'learning_rate': random.normalvariate(0.5, 0.5)}, parallelism=3),
    tensorboard={
      'log_dir': FLAGS.log_dir,
    }
)
def my_training_function(learning_rate):
  # some training logic
  ...
```

### Backends

Currently, MetaML supports two backends:
* `Native`: This is the default backend. Your trainings will be deployed using only Kubernete's `Job` object. This works with any Kubernetes cluster, but this backend only support 'embarassingly parallel' trainings.
* `Kubeflow`: This requires having [Kubeflow](https://github.com/kubeflow/kubeflow) pre-installed in your Kubernetes cluster. Trainings will be deployed using the `TfJob` custom object instead, allowing for distributed training. **The Kubeflow backend only supports TensorFlow at the moment**

### `@Train` decorator

The `Train` decorator takes 4 arguments:

* `package`: Defines the repository (this could be your DockerHub username, or something like `somerepo.acr.io` on Azure for example) and name that should be used to build the image. You can control wether you want to publish the image by setting `publish` to `True`.
* `strategy`: Specify which training strategy should be used (more details below).
* `architecture`: Specify which architecture should be used. (more details below)
* `tensorboard`: [Optional] If specified, will spawn an instance of TensorBoard to monitor your trainings
  * `log_dir`: Directory where the summaries are saved.
  * `pvc_name`: Name of an existing `PermanentVolumeClaim` that should be mounted.
  * `public`: If set to `True` then a public IP will be created for TensorBoard (provided your Kubernetes cluster supports this). Otherwise only a private IP will be created.

* `backend`: [Optionnal] Which backend to use. If not specified, the `Native` backend will be used.

#### Training Strategies

##### `BasicTrainingStrategy`

This is the default value for `strategy`. A single training run will be deployed. 

```python
# Note: we are note specifiying any strategy since this is the default value
@Train(package={'name': 'some_image_name', 'repository': 'some_docker_repo', 'publish': True})
def train_func():
  # some training logic
  ...
```

Complete example: [examples/simple-training/main.py](./examples/simple-training/main.py)


##### `HyperparameterTuning`
Allows you to run multiple trainings in parallel, each one with different values for your hyperparameters.

The `HyperparameterTuning` class takes 2 arguments:
* `hyperparameters`: This can either be a function returning a dictionnary or directly a dictionnanry.
* `runs`: Number of trainings that should be deployed

```python
from metaml.strategies import HyperparameterTuning

def gen_hp():
  return {'learning_rate': random.normalvariate(0.5, 0.5)}

@Train(
    package={'name': 'some_image_name', 'repository': 'some_docker_repo', 'publish': True},
    strategy=HyperparameterTuning(hyperparameters=gen_hp, runs=6),
)
def my_training_function(learning_rate):
  # some training logic
  ...
```

Complete example: [examples/hyperparameter-tuning/main.py](./examples/hyperparameter-tuning/main.py)


#### Training Architectures

###### `BasicArchitecture`

This is the default `architecture`, each training run will be a single container acting in isolation.

```python
# Note: we are note specifiying any architecture since this is the default value
@Train(package={'name': 'some_image_name', 'repository': 'some_docker_repo', 'publish': True})
def train_func():
  # some training logic
  ...
```

Complete example: [examples/simple-training/main.py](./examples/simple-training/main.py)


##### `DistributedTraining`

**Only supported with `Kubeflow` backend.**

This will start a [Distributed Training](https://www.tensorflow.org/deploy/distributed). 
Specify the number of desired parameter servers with `ps_count` and the number of workers with `worker_count`.
Another instance of type master will always be created.

```python
from metaml.architectures import DistribuedTraining
from metaml.backend import Kubeflow
@Train(
    package={'name': 'some_image_name', 'repository': 'some_docker_repo', 'publish': True},
    architecture=DistributedTraining(ps_count=2, worker_count=5),
    backend=Kubeflow
)
def train_func():
  # some training logic
  ...
```

See [https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config](https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config) to understand how you need to modify your model to support distributed training with Kubeflow.

Complete example: [examples/distributed-training/main.py](./examples/distributed-training/main.py)

### `@Serve` decorator

**This decorator is not yet fully implemented.**

The `@Serve` decorator allows you to mark the function that should be used for serving.
This function will automatically be encapsulated in a web server and deployed on Kubernetes.

```python
from metaml.serve import Serve

@Serve(package={'name': 'simple-serve', 'repository': 'wbuchwalter', 'publish': True})
def func():
  return "hello world"

func()
```

##### Arguments
`@Serve` takes 4 arguments:
* `package`: Same as for `@Train`
* `route`: [Optional] Which route should the web server serve on. Defaults to `/predict`
* `port`: [Optional] Which port should the web server listen on. Defaults to `8080`
* `replicas`: [Optional] How many replicas should be launched in parallel (they will all be deployed behind a load balanncer). Defaults to `1`.

## Installing

**This projects requires python 3**

#### `metaparticle-ast`

This project uses a fork of `metaparticle-ast` for now, that need to be installed from source as well:

```bash
go get github.com/metaparticle-io/metaparticle-ast
cd $GOPATH/src/github.com/metaparticle-io/metaparticle-ast
git remote add wbuchwalter https://github.com/wbuchwalter/metaparticle-ast
git pull wbuchwalter master

go get -d ./cmd/compiler/
rm -rf $GOPATH/src/github.com/kubeflow/tf-operator/vendor
go install ./cmd/compiler/mp-compiler.go
```

#### MetaML

```bash
git clone https://github.com/wbuchwalter/metaml
cd metaml
python setup.py install
```
