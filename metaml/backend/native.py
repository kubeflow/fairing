import json
import os
import subprocess
from metaml.backend.backend import Backend
from metaml.strategies import HyperparameterTuning
from metaml.architectures import DistributedTraining


class NativeBackend(Backend):

    def validate_training_options(self):
        if type(self.architecture) is DistributedTraining:
            raise Exception(
                "Distributed training is not implemented in the native backend. Use Kubeflow instead.")

    def compile_training_ast(self, img, name):
        svc = {
            "name": name,
            "guid": 1234567,
        }

        svc = self.compile_tensorboard(svc, name)

        svc = self.add_jobs(svc, name, img)

        return svc

    def compile_tensorboard(self, svc, name):
        if self.tensorboard_options:
            volumeMounts = [{
                "name": "tensorboard",
                "mountPath": self.tensorboard_options.log_dir
            }]
            volumes = [{
                "name": "tensorboard",
                "persistentVolumeClaim": self.tensorboard_options.pvc_name
            }]

            svc["services"] = [
                {
                    "name": "{}-tensorboard".format(name),
                    "replicas": 1,
                    "containers": [
                        {
                            "image": "tensorflow/tensorflow",
                            "command": ["tensorboard", "--host", "0.0.0.0", "--logdir", self.tensorboard_options.log_dir],
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
                "public": self.tensorboard_options.public
            }
        return svc

    def add_jobs(self, svc, name, img):
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
        svc["jobs"] = [
            {
                "name": name,
                #TODO should parallelism and completion be surfaced ? How would that be implemented in all backends
                "parallelism": self.strategy.runs,
                "completion": self.strategy.runs,
                "containers": [
                    {
                        "image": img,
                        "volumeMounts": volumeMounts
                    }
                ],
                "volumes": volumes
            }
        ]
        return svc

    def compile_serving_ast(self, img, name):
        svc = {
            "name": name,
            "guid": 456789,
        }

        svc["services"] = [
            {
                "name": "{}-metaml-serving".format(name),
                "replicas": 1,
                "containers": [
                    {
                        "image": img,
                    }
                ],
                # TODO: Use self.serving_options
                "ports": [{
                    'number': 80,
                    'protocol': 'TCP'
                }],
            }
        ]

        svc["serve"] = {
            "name": "{}-metaml-serving".format(name),
            "public": True
        }
        return svc
