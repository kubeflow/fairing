# Fairing

Easily train ML models on Kubernetes, directly from your python code.  
Fairing allows you to express how you want your model to be trained using python decorators.  

## Table of Contents

- [Requirements](#requirements)
- [Getting `fairing`](#getting-fairing)
- [Usage with Kubeflow](#usage-with-kubeflow)
  - [Simple TfJob](#simple-tfjob)
  - [Distributed Training](#distributed-training)
- [Usage with native Kubernetes](#usage-with-kubernetes)
  - [Simple Training](#simple-training)
- [From a Jupyter Notebook](#from-a-jupyter-notebook)

## Requirements

If you are going to use `fairing` on your local machine (as opposed to from a Jupyter Notebook deployed inside a Kubernetes cluster for example), you will need 
to have access to a deployed Kubernetes cluster, and have the `kubeconfig` for this cluster on your machine.

You will also need to have docker installed locally.

## Getting `fairing`

```bash
pip install fairing
```

Or, in a Jupyter Notebook, create a new cell and execute: `!pip install fairing`.

## Overview

`fairing` provides various class decorator allowing you to specify how you want your model to be packaged and trained.  
Your model needs to be defined as a class to work with `fairing`. 

This limitation is needed in order to enable usage of more complex training strategies and simplify usage from within a Jupyter Notebook.

Following are a series of example that should help you understand how fairing works.

## Usage with Kubeflow

### Simple TfJob

Instead of creating native `Job`s, `fairing` can leverage Kubeflow's `TfJob`s assuming you have Kubeflow installed in your cluster.

```python
import fairing
from fairing import builders
from fairing.training import kubeflow

DOCKER_REPOSITORY_NAME = '<your-repository-name>'
fairing.config.set_builder(builders.DockerBuilder(DOCKER_REPOSITORY_NAME))

@kubeflow.Training()
class MyModel(object):
    def train(self):
       # training logic
```

Complete example: [examples/kubeflow/main.py](./examples/kubeflow/main.py)

### Distributed Training

Using Kubeflow, we can also ask `fairing` to start [distributed trainings](https://www.tensorflow.org/deploy/distributed) instead:

```python
import fairing
from fairing.training import kubeflow
from fairing import builders

DOCKER_REPOSITORY_NAME = '<your-repository-name>'
fairing.config.set_builder(builders.DockerBuilder(DOCKER_REPOSITORY_NAME))

@kubeflow.DistributedTraining(worker_count=3, ps_count=1)
class MyModel(object):
    ...
```

Specify the number of desired parameter servers with `ps_count` and the number of workers with `worker_count`.
Another instance of type chief will always be created.

See [https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config](https://github.com/Azure/kubeflow-labs/tree/master/7-distributed-tensorflow#modifying-your-model-to-use-tfjobs-tf_config) to understand how you need to modify your model to support distributed training with Kubeflow.

Complete example: [examples/distributed-training/main.py](./examples/distributed-training/main.py)

### Usage with native Kubernetes

#### Simple Training

```python
from fairing.train import Train

@Train(repository='<your-repo-name>')
class MyModel(object):
    def train(self):
      # Training logic goes here

```

Complete example: [examples/simple-training/main.py](./examples/simple-training/main.py)

### From a Jupyter Notebook

To make `fairing` work from a Jupyter Notebook deployed with Kubeflow, a few more requirements are needed (such as Knative Build deployed).
Refer [to the dedicated documentation and example](examples/kubeflow-jupyter-notebook/).