import json
import os
import subprocess
from metaml.backend.backend import Backend

class KubeflowBackend(Backend):

    def compile_ast(self, img, name, train_options, tensorboard_options):
        volumes = []
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
                "replicaSpecs": [{
                    "replicaType": "MASTER",
                    "replicas": 1,
                    "containers": [
                    {
                        "image": img,
                        "volumeMounts": [{
                            "name": "tensorboard",
                            "mountPath": tensorboard_options.log_dir
                        }]}
                ],
                "volumes": volumes
                }]
            })

        svc["tfJobs"] = tfjobs
        return svc
