from fairing.backend.kubeflow import KubeflowBackend


class BasicArchitecture():
    def add_jobs(self, svc, count, img, name, volumes, volume_mounts):
        tfjobs = []
        for ix in range(count):
            tfjobs.append({
                "name": "{}-{}".format(name, ix),
                "replicaSpecs": [{
                    "replicaType": "MASTER",
                    "replicas": 1,
                    "containers": [
                        {
                            "image": img,
                            "volumeMounts": volume_mounts
                        }
                    ],
                    "volumes": volumes
                }]
            })

        svc["tfJobs"] = tfjobs
        return svc

    def get_associated_backend(self):
        return KubeflowBackend()
