from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()

import json
import os
import subprocess
from fairing.backend.backend import Backend
from fairing.strategies.hp import HyperparameterTuning
from fairing.metaparticle import MetaparticleClient

class NativeBackend(Backend):

    def add_tensorboard(self, svc, name, tb_options):
        if not tb_options:
            return svc, None, None
        volumeMounts = [{
            "name": "tensorboard",
            "mountPath": tb_options.log_dir
        }]
        volumes = [{
            "name": "tensorboard",
            "persistentVolumeClaim": tb_options.pvc_name
        }]

        svc["services"] = [
            {
                "name": "{}-tensorboard".format(name),
                "replicas": 1,
                "containers": [{
                        "image": "tensorflow/tensorflow",
                        "command": ["tensorboard", "--host", "0.0.0.0", "--logdir", tb_options.log_dir],
                        "volumeMounts": volumeMounts
                    }],
                "ports": [{
                    'number': 6006,
                    'protocol': 'TCP'
                }],
                "volumes": volumes
            }
        ]

        svc["serve"] = {
            "name": "{}-tensorboard".format(name),
            "public": tb_options.public
        }
        return svc, volumes, volumeMounts

    def compile_serving_ast(self, img, name, port, replicas):
        svc = {
            "name": name,
            "guid": 456789,
        }

        svc["services"] = [
            {
                "name": "{}-fairing-serving".format(name),
                "replicas": replicas,
                "containers": [
                    {
                        "image": img,
                    }
                ],
                # TODO: Use self.serving_options
                "ports": [{
                    'number': port,
                    'protocol': 'TCP'
                }],
            }
        ]

        svc["serve"] = {
            "name": "{}-fairing-serving".format(name),
            "public": True
        }
        return svc
    
    def stream_logs(self, image_name, image_tag):
        mp_client = MetaparticleClient()
        mp_client.logs("{name}-{tag}".format(name=image_name, tag=image_tag))
