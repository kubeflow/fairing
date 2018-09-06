from fairing.architectures.kubeflow.basic import BasicArchitecture
from fairing.backend.kubeflow import KubeflowBackend


class DistributedTraining(BasicArchitecture):
    def __init__(self, ps_count, worker_count):
        self.ps_count = ps_count
        self.worker_count = worker_count

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
                },
                    {
                    "replicaType": "WORKER",
                    "replicas": self.worker_count,
                    "containers": [
                        {
                            "image": img
                        }
                    ]
                },
                    {
                    "replicaType": "PS",
                    "replicas": self.ps_count,
                    "containers": [
                        {
                            "image": img
                        }]
                }]
            })

        svc["tfJobs"] = tfjobs
        return svc

    def get_associated_backend(self):
        return KubeflowBackend()
