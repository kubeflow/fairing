# Kubeflow Fairing E2E MNIST Case: Building, Training and Serving

You may see more details in the [Kubeflow examples mnist](https://github.com/kubeflow/examples/tree/master/mnist). The difference is that the example end-to-end takes Kubeflow Fairing to build docker image and launch TFJob for distributed training, and then create a InferenceService (KFServing CRD) to deploy model service.

This example guides you through:

- Taking an example TensorFlow model and modifying it to support distributed training.
- Using `Kubeflow Fairing` to build docker image and launch a `TFJob` to train model.
- Using `Kubeflow Fairing` to create `InferenceService` (KFServing CR) to deploy the trained model.
- Cleaning up the `TFJob` and `InferenceService` using `kubeflow-tfjob` and `kfserving` SDK client.

## Steps

1. Launch a Jupyter notebook

1. Open the notebook [mnist_e2e_on_prem.ipynb](mnist_e2e_on_prem.ipynb)

1. Follow the notebook to train and deploy MNIST on Kubeflow.
