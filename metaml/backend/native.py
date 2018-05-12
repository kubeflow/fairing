import json
import os
import subprocess
from metaml.backend.backend import Backend

class NativeBackend(Backend):

    def validate_options(self, train_options, tensorboard_options):
         if train_options.distributed_training:
            raise Exception("Distributed training is not implemented in the native backend. Use Kubeflow instead.")
            
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

        svc["jobs"] = [
            {
                "name": name,
                "parallelism": train_options.parallelism,
                "completion": train_options.completion if train_options.completion else train_options.parallelism,
                "containers": [
                    {
                        "image": img,
                        "volumeMounts": [{
                            "name": "tensorboard",
                            "mountPath": tensorboard_options.log_dir
                        }]}
                ],
                "volumes": volumes
            }
        ]

        return svc