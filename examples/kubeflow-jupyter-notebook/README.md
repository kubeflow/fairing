# Using `Fairing` with Kubeflow's TfJob inside a Jupyter Notebook

## Requirements

### Kubeflow

Kubeflow needs to be pre-installed in the cluster.

### Knative Build Component
A Knative Build controller needs to be deployed in the cluster beforehand to handle in-cluster builds.  
See: [Installing Knative Build Component](https://github.com/knative/docs/blob/master/build/installing-build-component.md)


### Container Registry Secret

A secret needs to be created to allow Knative to push to your registry

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: fairing-build
  annotations:
    build.knative.dev/docker-0: https://index.docker.io/v1/
type: kubernetes.io/basic-auth
data:
  username: <registry username>
  password: <registry password>
```

### Service Account

 ```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fairing-build
secrets:
  - name: fairing-build
```

### PermanentVolumeClaim

A `RWX` (Read Write Many) PVC named `fairing-build` also needs to be created beforehand.  
This allows the container hosting the notebook and the container doing the image build to share the needed context.  
For example, on Azure such a PVC can be created using Azure Files. 


### Mounting the Volume

Finally, the `fairing-build` PVC needs to be mounted into the container that hosts the Jupyter notebook at `/{USER}/.fairing/build-contexts`.

For example:

```yaml
containers:
- name: jupyter-tf
image: wbuchwalter/fairing-jupyter
volumeMounts:
    - name: src
    mountPath: /root/.fairing/build-contexts
volumes:
- name: src
    persistentVolumeClaim:
    claimName: fairing-build
```