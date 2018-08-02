# Fairing

Easily train and serve ML models on Kubernetes, directly from your python code.  

This projects uses [Metaparticle](http://metaparticle.io/) behind the scene.

fairing allows you to express how you want your model to be trained and served using native python decorators.  


## Training

The `Train` decorator takes 4 arguments:

* `package`: Defines the repository (this could be your DockerHub username, or something like `somerepo.acr.io` on Azure for example) and name that should be used to build the image. You can control wether you want to publish the image by setting `publish` to `True`.
* `strategy`: Specify which training strategy should be used (more details below).
* `architecture`: Specify which architecture should be used. (more details below)
* `tensorboard`: [Optional] If specified, will spawn an instance of TensorBoard to monitor your trainings
  * `log_dir`: Directory where the summaries are saved.
  * `pvc_name`: Name of an existing `PermanentVolumeClaim` that should be mounted.
  * `public`: If set to `True` then a public IP will be created for TensorBoard (provided your Kubernetes cluster supports this). Otherwise only a private IP will be created.

### Training Strategies

#### Basic Training

```python
from fairing.train import Train

@Train(package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True})
class MyModel(object):
    def train(self):
      # Training logic goes here

```
No `strategy` is specified here, since the default `strategy` is `basicTrainingStrategy`.

Complete example: [examples/simple-training/main.py](./examples/simple-training/main.py)


#### Hyperparameters Tuning
Allows you to run multiple trainings in parallel, each one with different values for your hyperparameters.

Your class should define a `hyperparameters` method that returns an dictionary of hyperparameters and their values.
This dictionary will be passed automatically passed to your `train` method.

```python
from fairing.train import Train
from fairing.strategies.hp import HyperparameterTuning

@Train(
    package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True},
    strategy=HyperparameterTuning(runs=6),
)
class MyModel(object):
    def hyperparameters(self):
      return {
        'learning_rate': random.normalvariate(0.5, 0.45)
      }

    def train(self, hp):
      # Training logic goes here
```

Complete example: [examples/hyperparameter-tuning/main.py](./examples/hyperparameter-tuning/main.py)

#### Population Based Training

```python
from fairing.train import Train
from fairing.strategies.pbt import PopulationBasedTraining

@Train(
    package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True},
    strategy=PopulationBasedTraining(
        population_size=10,
        exploit_count=6,
        steps_per_exploit=5000,
        pvc_name='<pvc-name>',
        model_path = MODEL_PATH
    )
)
class MyModel(object):
    def hyperparameters(self):
      # returns the dictionary of hyperparameters
    
    def build(self, hp):
      # build the model
    
    def train(self, hp):
      # training logic
    
    def save(self):
      # save the model at MODEL_PATH
    
    def restore(self, model_path):
      # restore the model from MODEL_PATH
```

Complete example: [examples/population-based-training/main.py](./examples/population-based-training/main.py)


### Training Architectures

#### Basic Architure

This is the default `architecture`, each training run will be a single container acting in isolation.
No `architecure` is specified since this is the default value.

```python
# Note: we are note specifiying any architecture since this is the default value
@Train(package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True})
class MyModel(object):
    ...
```

Complete example: [examples/simple-training/main.py](./examples/simple-training/main.py)


#### Distributed Training

> Note: This architecture is currently only supported with [Kubeflow](https://github.com/kubeflow/kubeflow). So you need to have Kubeflow deployed in your Kubernetes cluster 


```python
from fairing.train import Train
from fairing.architectures.kubeflow.distributed import DistributedTraining

@Train(
    package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True},
    architecture=DistributedTraining(ps_count=2, worker_count=5),
)
class MyModel(object):
    ...
```

This will start a [Distributed Training](https://www.tensorflow.org/deploy/distributed). 

Specify the number of desired parameter servers with `ps_count` and the number of workers with `worker_count`.
Another instance of type master will always be created.

See [https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config](https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config) to understand how you need to modify your model to support distributed training with Kubeflow.

Complete example: [examples/distributed-training/main.py](./examples/distributed-training/main.py)

### TensorBoard

You can easily attach a TensorBoard instance to monitor your training:

```python
@Train(
    package={'name': '<your-image-name>', 'repository': '<your-repo-name>', 'publish': True},
    tensorboard={
      'log_dir': LOG_DIR,
      'pvc_name': '<pvc-name>',
      'public': True # Request a public IP
    }
)
class MyModel(object):
    ...
```

## Serving

:warning: **This decorator is not yet implemented.** :warning:

The `@Serve` decorator allows you to mark the function that should be used for serving.
This function will automatically be encapsulated in a web server and deployed on Kubernetes.

```python
from fairing.serve import Serve

@Serve(package={'name': 'simple-serve', 'repository': 'wbuchwalter', 'publish': True})
class MyModel(object):
    
    def build(self):
      # build the model
    
    def restore(self, model_path):
      # restore the model from MODEL_PATH

    def serve(self, request):
      # return prediction
```

##### Arguments
`@Serve` takes 4 arguments:
* `package`: Same as for `@Train`
* `route`: [Optional] Which route should the web server serve on. Defaults to `/predict`
* `port`: [Optional] Which port should the web server listen on. Defaults to `8080`
* `replicas`: [Optional] How many replicas should be launched in parallel (they will all be deployed behind a load balanncer). Defaults to `1`.

## Installing

**Note**: This projects requires python 3

**metaparticle-ast**

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

**fairing**

```bash
pip install fairing
```
