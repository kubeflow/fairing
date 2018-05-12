import json
import os
import subprocess
from metaml.backend.native import NativeBackend
from metaml.architectures import DistributedTraining

class KubeflowBackend(NativeBackend):

    def validate_training_options(self):
        pass

    def add_jobs(self, svc, name, img):
        tfjobs = []
        for ix in range(self.strategy.runs):
            tfjobs.append({
                "name": "{}-{}".format(name, ix),
                "replicaSpecs": self.build_replica_specs(img)
            })

        svc["tfJobs"] = tfjobs
        return svc        

    def build_replica_specs(self, img):
        replica_specs = []
        volumeMounts = []
        volumes = []
        if self.tensorboard_options:
            volumeMounts = [{
                "name": "tensorboard",
                "mountPath": self.tensorboard_options.log_dir
            }] 
            volumes = [{
                "name": "tensorboard",
                "persistentVolumeClaim": self.tensorboard_options.pvc_name
            }]

        replica_specs.append({
            "replicaType": "MASTER",
            "replicas": 1,
            "containers": [
                {
                    "image": img,
                    "volumeMounts": volumeMounts
                }
            ],
            "volumes": volumes
        })

        if type(self.architecture) is DistributedTraining:
            replica_specs.append({
                "replicaType": "WORKER",
                "replicas": self.architecture.worker_count,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })
            replica_specs.append({
                "replicaType": "PS",
                "replicas": self.architecture.ps_count,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })

        return replica_specs
