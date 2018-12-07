# Using `Fairing` with Kubeflow's TfJob inside a Jupyter Notebook

This uses the appender builder and the jupyter-notebook service account to push and run a training job through Kubeflow's TfJob.

## Requirements

### Kubeflow


There are three parameters that are set with the builder
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