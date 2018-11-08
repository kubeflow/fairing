## Development

You'll need

* Docker
* kubectl configured
* a Kubernetes Cluster

### With Skaffold

You can download the latest skaffold 
Linux
```
curl -Lo skaffold https://storage.googleapis.com/skaffold/builds/latest/skaffold-linux-amd64 && chmod +x skaffold && sudo mv skaffold /usr/local/bin
```
Darwin
```
curl -Lo skaffold https://storage.googleapis.com/skaffold/builds/latest/skaffold-darwin-amd64 && chmod +x skaffold && sudo mv skaffold /usr/local/bin
```
Windows
https://storage.googleapis.com/skaffold/builds/latest/skaffold-windows-amd64.exe


Simply run

```bash
// Where $REGISTRY is the prefix of a docker container registry you can push to
skaffold config set default-repo $REGISTRY
```

```bash
skaffold dev
```

And access the notebook on `localhost:8888`. Python files in `fairing-py` will be synced to the running container, while changes to the `fairing` Go binary will force a rebuild and redeploy of the notebook.


### Without Skaffold

1. Make changes
2. Rebuild the the image where $REGISTRY is a docker registry you have push access to.
`docker build -t $REGISTRY/fairing:$TAG`
3. Push the image `docker push $REGISTRY/fairing:$TAG`
4. Run the deployment `kubectl apply -f k8s`
5. Port forward the deployment using `kubectl port-forward -n kubeflow notebook`

### Without Kubeflow

Without Kubeflow, you'll need to create a secret called `user-gcp-sa` that contains the GCP credentials needed to push an image to the registry.



