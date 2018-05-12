import json
import os
import subprocess
from metaml.backend.backend import Backend


class KubeflowBackend(Backend):

    def validate_options(self, train_options, tensorboard_options):
        pass

    def compile_ast(self, img, name, train_options, tensorboard_options):
        svc = {
            "name": name,
            "guid": 1234567,
        }

        if tensorboard_options:
            volumeMounts = [{
                "name": "tensorboard",
                "mountPath": tensorboard_options.log_dir
            }]
            volumes = [{
                "name": "tensorboard",
                "persistentVolumeClaim": tensorboard_options.pvc_name
            }]

            svc["services"] = [
                {
                    "name": "{}-tensorboard".format(name),
                    "replicas": 1,
                    "containers": [
                        {
                            "image": "tensorflow/tensorflow",
                            "command": ["tensorboard", "--host", "0.0.0.0", "--logdir", tensorboard_options.log_dir],
                            "volumeMounts": volumeMounts
                        }
                    ],
                    "ports": [{
                        'number': 6006,
                        'protocol': 'TCP'
                    }],
                    "volumes": volumes
                }
            ]

            svc["serve"] = {
                "name": "{}-tensorboard".format(name),
                "public": tensorboard_options.public
            }

        tfjobs = []
        for ix in range(train_options.parallelism):
            tfjobs.append({
                "name": "{}-{}".format(name, ix),
                "replicaSpecs": self.build_replica_specs(img, train_options, tensorboard_options)
            })

        svc["tfJobs"] = tfjobs
        return svc

    def build_replica_specs(self, img, train_options, tb_options):
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

        if train_options.distributed_training:
            replica_specs.append({
                "replicaType": "WORKER",
                "replicas": train_options.distributed_training.worker,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })
            replica_specs.append({
                "replicaType": "PS",
                "replicas": train_options.distributed_training.ps,
                "containers": [
                    {
                        "image": img
                    }
                ]
            })

        return replica_specs
