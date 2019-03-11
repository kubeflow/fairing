# Fairing

Easily train ML models on Kubernetes, directly from your python code, or a Jupyter notebook.

## Requirements

- a kubeconfig
- a docker config

If you already have Docker and kubectl configured, you're all set! If you are using [Kubeflow](https://github.com/kubeflow/kubeflow), you can take advantage of advanced features.

## Installing `fairing`

```bash
pip install git+https://github.com/kubeflow/fairing@master
```

## Overview

`fairing` provides functions to seemlessly train models remotely on Kubernetes clusters.

Features
* Build images in seconds (without Docker)
* Run training jobs on Kubernetes without writing Dockerfiles or Kubernetes Manifests

### Example

Create a simple Tensorflow model that prints out the hostname of the machine

```python
import os
import fairing
import tensorflow as tf


class SimpleModel():
    def train(self):
        hostname = tf.constant(os.environ['HOSTNAME'])
        sess = tf.Session()
        print('Hostname: ', sess.run(hostname).decode('utf-8'))

if __name__ == '__main__':
    model = SimpleModel()
    model.train()    
```

If you have `GOOGLE_APPLICATION_CREDENTIALS` set, you can skip the next step. Otherwise, set the builder
```python
fairing.config.set_builder(name='append', registry='<your-registry-here>')
````

Now, run the training job remotely with
```
fairing.config.run()
```

What happened?
Fairing

- Packaged your code in a docker container (without using docker)
- Deployed a Kubernetes workload with the training job
- Streamed those logs back to you in real time

#### Configuring Fairing

There are three configurable parts of fairing. 

The **preprocessor** defines how a set of inputs gets mapped to a context for the docker image build. It can convert input files, exclude some, and change the entrypoint.

The **builder** defines how and where an image gets built. There are different strategies that will make sense for different environments and use cases.

The **deployer** defines how a training job gets launched. It uses the image produced by the builder to run the training job on Kubernetes.

| Builders |  |
|:--------:|:--------------------------------------------------------------------------------------------------------------------------------------------------------:|
| Append | Append the code as a new layer on an existing docker image. The base image won't be pulled and only the delta will be pushed to the registry. Very fast. |
| Cluster | Launch a build job in the Kubernetes cluster itself. Build and push a container in a container. |
| Docker | Uses a local docker daemon to build and push the image. |


| Deployers |  |
|:---------:|:-------------------------------------------------------------------------:|
| Job | Uses a Kubernetes Job resource to launch the training job |
| TfJob | Uses a Kubeflow Tensorflow Job custom resource to launch the training job |



| Preprocessors |  |
|:-------------:|:--------------------------------------------------------------------------------:|
| python | Takes input files and copies them directly into the container. |
| notebook | Converts a notebook into a runnable python file. Strips out the non-python code. |
| full_notebook | Runs a full notebook as-is |
