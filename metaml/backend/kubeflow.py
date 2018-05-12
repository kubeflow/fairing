import json
import os
import subprocess
from metaml.backend.native import NativeBackend
from metaml.strategies import DistributedTraining


class KubeflowBackend(NativeBackend):

    def validate_training_options(self, strategy, tensorboard_options):
        pass

    def add_jobs(self, svc, name, img, strategy, tensorboard_options):
        tfjobs = []
        for ix in range(strategy.parallelism):
            tfjobs.append({
                "name": "{}-{}".format(name, ix),
                "replicaSpecs": self.build_replica_specs(img, strategy, tensorboard_options)
            })

        svc["tfJobs"] = tfjobs
        return svc        

    def build_replica_specs(self, img, strategy, tb_options):
        replica_specs = []
        volumeMounts = [{
            "name": "tensorboard",
            "mountPath": tb_options.log_dir
        }]
        volumes = [{
            "name": "tensorboard",
            "persistentVolumeClaim": tb_options.pvc_name
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

        if type(strategy) is DistributedTraining:
            replica_specs.append({
                "replicaType": "WORKER",
                "replicas": strategy.worker_count,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })
            replica_specs.append({
                "replicaType": "PS",
                "replicas": strategy.ps_count,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })

        return replica_specs
