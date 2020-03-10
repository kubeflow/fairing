# 2020 Roadmap

1. Fairing 1.0 release (P1, 2020 Q2)
   - Improve Fairing quality for 1.0 production readiness, and enhance testing and examples.
   - Enhancement [API Documents](https://kubeflow-fairing.readthedocs.io/en/latest/index.html).
   - Deprecating high level API `ml_tasks`, maybe warn the deprecating in 1.0 release.

2. Fairing provides a python SDK for Kubeflows components
   - Support Tekton (P1, 2020 Q2).
   - More generic interacts with Kubernetes such as bulk apply YAML Specs (P1, 20202 Q2).
   - Support more builder such as podman or s2i and more backends such as IBM Cloud (P2, 20202 Q2-Q3)
   - Intergration with other kubeflow components such as Katib and more frameworks etc. (P2, 2020 Q3-Q4).
   - Add istio routing rules in Fairing (P2, 2020 Q3-Q4)

3. Generate one single SDK for Kubeflow components (P2 2020 Q3-Q4).
   - Consider and make an auto mechanism to generate Kubeflow master SDK (maybe better to name `kubeflow`).
   - Reconcile the APIs of kubeflow components and satisfy ML logical manner.
