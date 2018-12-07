# Using `Fairing` with Kubeflow's TfJob inside a Jupyter Notebook

This uses the appender builder and the jupyter-notebook service account to push and run a training job through Kubeflow's TfJob.

## Requirements

- Kubeflow on GKE

## Instructions

In the JupyterHub UI, use create a new instance of jupyter with `gcr.io/kubeflow-images-public/fairing:v0.0.1` as the image.

This will only work on newer versions of Kubeflow. To use this on 0.3.x, you need to manually give `jupyter-notebook-role` `pods/log` permission.

On 0.3.x, from this directory apply the pre-0.4-patch.yaml to the cluster with 

`kubectl apply -f pre-0.4-patch.yaml`

In the notebook, there are three parameters to be set.
```
DOCKER_REPOSITORY_NAME = 'gcr.io/mrick-gcp'
BASE_IMAGE='gcr.io/kubeflow-images-public/fairing:v0.0.1'
NOTEBOOK_FILE = '/home/jovyan/work/demo.ipynb'
```

Change `DOCKER_REPOSITORY_NAME` to match your project that the Kubeflow cluster is currently running in.
```
DOCKER_REPOSITORY_NAME = 'gcr.io/<your-project-here>'
```

If you name your notebook differently, update the filename in 
```
NOTEBOOK_FILE = '/home/jovyan/work/<your filename>.ipynb'
```

Then, just run the cell. The builder will convert the notebook to a python file, append it on top of the base image and 