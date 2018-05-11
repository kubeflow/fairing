import json
import os
import subprocess


class Backend:
    def cancel(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--delete'])

    def logs(self, name):
        subprocess.check_call(
            ['mp-compiler', '-f', '.metaparticle/spec.json', '--deploy=false', '--attach=true'])

    def compile_ast(self, img, name, train_options, tensorboard_options):
      raise NotImplementedError()
    
    def run(self, img, name, train_options, tensorboard_options):
        svc = self.compile_ast(img, name, train_options, tensorboard_options)

        if not os.path.exists('.metaparticle'):
            os.makedirs('.metaparticle')

        with open('.metaparticle/spec.json', 'w') as out:
            json.dump(svc, out)
        
        subprocess.check_call(['mp-compiler', '-f', '.metaparticle/spec.json'])     