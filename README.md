# Kubeflow Fairing

Easily build, train, and deploy your machine learning (ML) training jobs on Kubeflow or Kubernetes,
directly from Python code or a Jupyter notebook. 

## Requirements

To use Kubeflow Fairing, you need:

- a kubeconfig
- a docker config

If you already have Docker and kubectl configured, you're all set! If you are using
[Kubeflow](https://www.kubeflow.org/), you can take advantage of advanced features,
such as using [TFJob](https://www.kubeflow.org/docs/components/tftraining/) to train
a TensorFlow model.

## Installing Kubeflow Fairing

To install Kubeflow Fairing from PyPI:

```bash
pip install git+https://github.com/kubeflow/fairing@master
```

## Example

This example demonstrates how to create a simple TensorFlow model and train it locally.
Then it illustrates how to use Kubeflow Fairing to package the model and run it on
Kubernetes.

1. Create a simple TensorFlow model that prints the machine's hostname.

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

2. Configure the strategy that Kubeflow Fairing will use to package the model.
   If you are using Google Cloud Platform and you have [set the _GOOGLE_
   APPLICATION_CREDENTIALS_ environmental variable][gcp-auth], you can skip this
   step. Otherwise, use `set_builder()` to configure the builder method with
   the strategy you want to use to build the container image and the location
   of the registry to store the container image in.

```python
fairing.config.set_builder(name='append', registry='<your-registry-here>')
````

- `name`: The builder strategy name: **append**, **cluster**, or **docker**. 
- `registry`: The location of your container image registry.

3. Run the training job remotely on Kubernetes.

```
fairing.config.run()
```

In this example, Kubeflow Fairing:

- Packaged your code in a docker container, without using docker.
- Deployed your training job as a Kubernetes workload.
- Streamed the logs from the training job back to you in real time.

## Configuring Kubeflow Fairing

There are three configurable parts of Kubeflow Fairing: the preprocessor,
builder, and deployer. 

The **preprocessor** defines how a set of inputs gets mapped to a context
for the docker image build. It can convert input files, exclude some, and
change the entrypoint for the training job.

- **python:** Copies the input files directly into the container image.
- **notebook:** Converts a notebook into a runnable python file. Strips
  out the non-python code.
- **full_notebook:** Runs a full notebook as-is, including bash scripts
  or non-Python code.

The **builder**  defines how and where a container image is built. There
are different strategies that will make sense for different environments
and use cases.

- **append:** Creates a Dockerfile by appending the your code as a new
  layer on an existing docker image. This builder requires less to time
  to create a container image for your training job, because the base
  image is not pulled to create the image and only the differences are
  pushed to the container image registry. 
- **cluster:** Builds the container image for your training job in the
  Kubernetes cluster. This option is useful for building jobs in
  environments where a Docker daemon is not present, for example a
  hosted notebook.
- **docker:** Uses a local docker daemon to build and push the container
  image for your training job to your container image registry.

The **deployer** defines how a training job gets launched. It uses the
image produced by the builder to run the training job on Kubernetes.

- **Job:** Uses a Kubernetes Job resource to launch your training job.
- **TfJob:** Uses the TFJob component of Kubeflow to launch your
  Tensorflow training job.

[gcp-auth]: https://cloud.google.com/docs/authentication/getting-started#auth-cloud-implicit-python
