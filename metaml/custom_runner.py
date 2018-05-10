import json
import os
import subprocess


class CustomRunnner:
    def cancel(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])

    def ports(self, portArray):
        result = []
        for port in portArray:
            result.append({
                'number': port,
                'protocol': 'TCP'
            })
        return result

    def compile_ast(self, img, name, train_options):
        svc = {
            "name": name,
            "guid": 1234567,
        }

        svc["jobs"] = [
            {
                "name": name,
                "replicas": train_options.parallelism,
                "containers": [
                    {"image": img}
                ]
            }
        ]

        if train_options.tensorboard:
          svc["services"] = [
            {
              "name": "{}-tensorboard".format(name),
              "replicas": 1,
              "containers": [
                {"image": "tensorflow/tensorflow"}
              ],
              "ports": [{
                'number': 6006,
                'protocol': 'TCP'
              }]
            }
          ]

          svc["serve"] = {
            "name": "{}-tensorboard".format(name),
            # always public for now
            "public": True
          }

        return svc

    def run(self, img, name, train_options):
        svc = self.compile_ast(img, name, train_options)

        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)

        subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])
