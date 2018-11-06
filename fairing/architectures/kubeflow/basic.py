from fairing.backend.kubeflow import KubeflowBackend
from fairing.utils import get_image_full

class BasicArchitecture():
    def add_jobs(self, svc, count, repository, image_name, image_tag, volumes, volume_mounts):
        full_image_name = get_image_full(repository, image_name, image_tag)
        tfjobs = []
        for ix in range(count):
            tfjobs.append({
                "name": "{}-{}-{}".format(image_name, image_tag, ix),
                "replicaSpecs": [{
                    "replicaType": "MASTER",
                    "replicas": 1,
                    "containers": [
                        {
                            "image": full_image_name,
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
