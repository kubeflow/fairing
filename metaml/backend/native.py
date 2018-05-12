import json
import os
import subprocess
from metaml.backend.backend import Backend
from metaml.strategies import DistributedTraining, HyperparameterTuning

class NativeBackend(Backend):

    def validate_training_options(self, strategy, tensorboard_options):
         if type(strategy) is DistributedTraining:
            raise Exception("Distributed training is not implemented in the native backend. Use Kubeflow instead.")

    def compile_training_ast(self, img, name, strategy, tensorboard_options):
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
        
        svc = self.add_jobs(svc, name, img, strategy, tensorboard_options)

        return svc
    
    def add_jobs(self, svc, name, img, strategy, tensorboard_options):
        if not type(strategy) is HyperparameterTuning:
            raise Exception('{} strategy is not supported by Native backend'.format(type(strategy)))
        
        volumeMounts = [{
            "name": "tensorboard",
            "mountPath": tensorboard_options.log_dir
        }]
        volumes = [{
            "name": "tensorboard",
            "persistentVolumeClaim": tensorboard_options.pvc_name
        }]
        svc["jobs"] = [
            {
                "name": name,
                "parallelism": strategy.parallelism,
                "completion": strategy.completion,
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

    def compile_serving_ast(self, img, name, serving_options):
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

    
