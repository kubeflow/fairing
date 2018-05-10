import json
import os
import subprocess


class NativeRunnner:
    def cancel(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])

    def compile_ast(self, img, name, train_options, tensorboard_options):

        volumes = []
        volumeMounts = []
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
                        {"image": "tensorflow/tensorflow",
                         "volumeMounts": volumeMounts}
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
                "replicas": train_options.parallelism,
                "containers": [
                    {"image": img, "volumeMounts": volumeMounts}
                ],
                "volumes": volumes
            }
        ]

        return svc

    def run(self, img, name, train_options, tensorboard_options):
        svc = self.compile_ast(img, name, train_options, tensorboard_options)

        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)

        subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])
